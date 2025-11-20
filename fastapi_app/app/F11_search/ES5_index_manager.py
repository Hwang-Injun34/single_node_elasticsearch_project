import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from app.F11_search.ES1_client import es_async, es_sync
from app.F11_search.ES2_index_mapping import INDEX_MAPPING

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def create_index_if_not_exists(index_name: str):
    """
    주어진 이름의 Elasticsearch 인덱스가 존재하지 않으면 생성합니다.
    인덱스가 이미 존재하면 아무 작업도 수행하지 않습니다.

    Args:
        index_name: 생성할 인덱스의 이름.
    """
    try:
        if es_async:
            # 비동기 클라이언트로 인덱스 존재 여부 확인
            if await es_async.indices.exists(index=index_name):
                logger.info(f"Index '{index_name}' already exists. Skipping creation.")
                return
            
            # 인덱스 생성
            logger.info(f"Index '{index_name}' not found. Attempting to create...")
            await es_async.indices.create(
                index=index_name,
                body=INDEX_MAPPING,
                request_timeout=30
            )

        else:  # 동기 클라이언트 사용
            if es_sync.indices.exists(index=index_name):
                logger.info(f"Index '{index_name}' already exists. Skipping creation.")
                return

            logger.info(f"Index '{index_name}' not found. Attempting to create...")
            es_sync.indices.create(
                index=index_name,
                body=INDEX_MAPPING,
                request_timeout=30
            )
        
        logger.info(f"Successfully created index '{index_name}'.")

    except Exception as e:
        # Tenacity가 재시도할 수 있도록 에러를 다시 발생시킵니다.
        logger.error(f"Failed to create index '{index_name}': {e}", exc_info=True)
        raise
