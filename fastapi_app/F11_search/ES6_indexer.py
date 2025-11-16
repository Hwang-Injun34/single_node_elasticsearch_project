# app/F11_search/ES6_reindexing_runner.py
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload

from elasticsearch.helpers import async_bulk

from app.F11_search.ES1_client import es_async
from app.F11_search.ES3_doc_converter import convert_feed_to_document
from app.F11_search.ES4_alias_manager import switch_aliases_to_new_index
from app.F11_search.ES5_index_manager import create_index_if_not_exists
from app.F7_models.feeds import Feed
from app.F5_core.config import settings

logger = logging.getLogger(__name__)

# --- 내부 헬퍼 함수: 데이터베이스에서 데이터를 스트리밍하고 변환 ---

async def _prepare_bulk_actions(db: AsyncSession, index_name: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    데이터베이스에서 Feed 데이터를 스트리밍하여 Elasticsearch bulk action 형식으로 변환하고 yield합니다.
    메모리 사용량을 최소화하기 위해 모든 데이터를 한 번에 로드하지 않습니다.
    """
    logger.info("Starting to stream and convert data from the database...")
    
    # [성능 개선 1] N+1 문제를 방지하기 위해 Eager Loading 적용
    query = (
        select(Feed)
        .options(
            joinedload(Feed.organization),
            joinedload(Feed.category),
            selectinload(Feed.ratings),
            selectinload(Feed.bookmarks)
        )
    )

    # [성능 개선 2] .all() 대신 stream_scalars를 사용하여 메모리 효율적으로 처리
    stream = await db.stream_scalars(query)
    
    count = 0
    async for feed in stream:
        try:
            doc = convert_feed_to_document(feed)
            if doc:
                yield {
                    "_op_type": "index",
                    "_index": index_name,
                    "_id": doc["id"],
                    "_source": doc,
                }
                count += 1
                if count % 1000 == 0:
                    logger.info(f"{count} documents prepared for indexing...")
        except Exception as e:
            logger.error(f"Error converting Feed ID {feed.id}: {e}", exc_info=True)
            # 단일 문서 변환 실패 시 전체 프로세스를 중단합니다.
            raise

    logger.info(f"Finished preparing a total of {count} documents.")


# --- 외부 호출용 메인 함수: 재색인 오케스트레이터 ---

async def run_reindexing(db: AsyncSession):
    """
    전체 재색인 파이프라인을 실행합니다.
    1. 새 인덱스 생성
    2. DB에서 데이터를 스트리밍하여 새 인덱스로 Bulk 색인
    3. 성공 시 Alias를 새 인덱스로 전환
    """
    # [수정] Pylance 경고 해결: try 블록 밖에서 변수 초기화
    new_index_name: str = ""
    
    try:
        # 1. 새 인덱스 생성 (타임스탬프 기반)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        new_index_name = f"{settings.ELASTICSEARCH_INDEX_PREFIX}_{timestamp}"
        await create_index_if_not_exists(new_index_name)

        # 2. Bulk 색인 실행
        actions_iterator = _prepare_bulk_actions(db, new_index_name)
        
        # async_bulk는 iterator를 지원하므로 메모리 효율적입니다.
        success, failed = await async_bulk(
            client=es_async,
            actions=actions_iterator,
            raise_on_error=False  # 실패 내역을 직접 처리하기 위해 False로 설정
        )

        logger.info(f"Indexing attempted: {success + len(failed)}, Success: {success}, Failed: {len(failed)}")

        # 실패한 항목이 있으면 상세 원인을 로깅하고 프로세스 중단
        if failed:
            logger.error("★★★★★ Bulk indexing failed for some documents: ★★★★★")
            for i, fail_item in enumerate(failed[:5]): # 최대 5개만 로깅
                logger.error(f"  - Failure {i+1}: {fail_item}")
            raise Exception(f"Bulk indexing failed. See logs. New index '{new_index_name}' will not be used.")
        
        if success == 0:
            logger.warning("No documents were indexed. Check the database and converter. Skipping alias switch.")
            return

        # 3. Alias 전환
        aliases_to_switch = [settings.ELASTICSEARCH_READ_ALIAS, settings.ELASTICSEARCH_WRITE_ALIAS]
        await switch_aliases_to_new_index(new_index_name, aliases_to_switch)
        
        logger.info(f"Re-indexing completed successfully. Alias switched to new index: '{new_index_name}'")

    except Exception as e:
        logger.error(f"Re-indexing pipeline failed: {e}", exc_info=True)
        # [수정] new_index_name이 할당된 경우에만 로그를 남겨 안전성 확보
        if new_index_name:
            logger.warning(f"The new index '{new_index_name}' was created but the process failed. It will not be used.")
        # 에러를 다시 발생시켜 호출한 쪽에서 실패를 인지하도록 함
        raise