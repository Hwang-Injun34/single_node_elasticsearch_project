# app/F11_search/ES9_cleanup.py
import logging
from typing import Dict, Any, Set

from elasticsearch import NotFoundError  # [추가] NotFoundError 임포트

from app.F11_search.ES1_client import es_async, es_sync
from app.F5_core.config import settings

logger = logging.getLogger(__name__)

# --- 내부 헬퍼 함수 ---

def _get_indices_to_delete(all_indices_details: Dict[str, Any], active_indices: Set[str], keep_count: int) -> list[str]:
    """
    삭제할 인덱스와 보존할 인덱스를 결정합니다.

    Args:
        all_indices_details: 모든 인덱스의 상세 정보 (ES get() API 결과).
        active_indices: 현재 활성 alias에 연결된 인덱스 이름 집합.
        keep_count: 최소 보존할 인덱스의 개수.

    Returns:
        삭제 대상 인덱스 이름의 리스트.
    """
    # 1. 현재 사용 중인(alias에 연결된) 인덱스는 삭제 대상에서 제외합니다.
    inactive_indices = {
        name: details for name, details in all_indices_details.items()
        if name not in active_indices
    }

    if not inactive_indices:
        logger.info("No inactive indices found to clean up.")
        return []

    # 2. 비활성 인덱스를 생성 시간(creation_date) 기준으로 최신순으로 정렬합니다.
    sorted_inactive_indices = sorted(
        inactive_indices.keys(),
        key=lambda name: int(inactive_indices[name]['settings']['index']['creation_date']),
        reverse=True
    )
    
    # 3. 보존할 인덱스(keep_count)를 제외한 나머지를 삭제 대상으로 선정합니다.
    indices_to_delete = sorted_inactive_indices[keep_count:]
    indices_to_keep = sorted_inactive_indices[:keep_count]

    if indices_to_keep:
        logger.info(f"Keeping recent inactive indices (for rollback): {indices_to_keep}")
    if indices_to_delete:
        logger.info(f"Indices marked for deletion: {indices_to_delete}")
    else:
        logger.info("No old indices to delete based on the retention policy.")
        
    return indices_to_delete

# --- 외부 호출용 메인 함수 ---

async def cleanup_old_indices(keep_count: int = 3):
    """
    오래된 비활성 인덱스를 정리합니다. 현재 활성 alias에 연결된 인덱스는 절대 삭제하지 않습니다.

    Args:
        keep_count: 롤백 등을 위해 최소한으로 보존할 최신 비활성 인덱스의 개수.
    """
    logger.info(f"Starting cleanup process for old indices. Keeping at least {keep_count} recent inactive indices.")
    
    try:
        if not es_async:
            # 동기 클라이언트 로직은 생략되었습니다. 필요시 추가해야 합니다.
            raise RuntimeError("Asynchronous Elasticsearch client is not available.")
            
        # 1. 패턴에 맞는 모든 인덱스의 상세 정보를 가져옵니다.
        try:
            all_indices_details = await es_async.indices.get(index=f"{settings.ELASTICSEARCH_INDEX_PREFIX}_*")
        except NotFoundError:
            logger.info("No indices found with the specified prefix. Cleanup finished.")
            return

        # 2. 현재 활성 alias가 가리키는 인덱스 목록을 안전하게 가져옵니다.
        active_indices: Set[str] = set()
        try:
            # [수정] READ_ALIAS가 없을 수도 있으므로 try...except로 감쌉니다.
            read_alias_details = await es_async.indices.get_alias(name=settings.ELASTICSEARCH_READ_ALIAS)
            active_indices.update(read_alias_details.keys())
        except NotFoundError:
            logger.warning(f"Read alias '{settings.ELASTICSEARCH_READ_ALIAS}' not found, skipping.")

        try:
            # [수정] WRITE_ALIAS가 없을 수도 있으므로 try...except로 감쌉니다.
            write_alias_details = await es_async.indices.get_alias(name=settings.ELASTICSEARCH_WRITE_ALIAS)
            active_indices.update(write_alias_details.keys())
        except NotFoundError:
            logger.warning(f"Write alias '{settings.ELASTICSEARCH_WRITE_ALIAS}' not found, skipping.")

        if not active_indices:
            logger.info("No active aliases found.")
        else:
            logger.info(f"Currently active indices (in-use): {list(active_indices)}")

        # 3. 삭제할 인덱스 목록을 결정합니다.
        indices_to_delete = _get_indices_to_delete(all_indices_details, active_indices, keep_count)

        # 4. 결정된 인덱스들을 삭제합니다.
        if not indices_to_delete:
            logger.info("Cleanup finished. Nothing to delete.")
            return

        response = await es_async.indices.delete(index=",".join(indices_to_delete), ignore_unavailable=True)
        
        if response.get("acknowledged"):
            logger.info(f"Successfully deleted old indices: {indices_to_delete}")
        else:
            logger.warning(f"Deletion request for {indices_to_delete} was not acknowledged. Response: {response}")

    except Exception as e:
        logger.error(f"An error occurred during index cleanup: {e}", exc_info=True)
        raise