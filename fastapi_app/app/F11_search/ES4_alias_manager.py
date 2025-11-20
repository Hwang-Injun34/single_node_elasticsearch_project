# app/F11_search/alias_manager.py
import logging
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential
from elasticsearch import NotFoundError  # 명확한 예외 처리를 위해 import

from app.F11_search.ES1_client import es_async, es_sync
from app.F5_core.config import settings

logger = logging.getLogger(__name__)

# --- 내부 헬퍼 함수 (단일 alias 전환 로직) ---

async def _switch_single_alias_async(new_index_name: str, alias: str):
    """(비동기) 단일 alias를 새 인덱스로 원자적으로 전환합니다."""
    actions = []
    try:
        # 1. 현재 alias에 연결된 모든 이전 인덱스를 찾습니다.
        alias_response = await es_async.indices.get_alias(name=alias)
        current_indices = list(alias_response.keys())
        
        # 2. 이전 인덱스들에서 alias를 제거하는 액션을 추가합니다.
        for index in current_indices:
            actions.append({"remove": {"index": index, "alias": alias}})
            
    except NotFoundError:
        # alias가 존재하지 않는 경우는 정상적인 상황(최초 생성)이므로 경고만 로깅합니다.
        logger.warning(f"Alias '{alias}' not found. It will be created on the new index '{new_index_name}'.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while getting alias '{alias}': {str(e)}")
        raise  # 에러를 다시 발생시켜 @retry가 동작하도록 함

    # 3. 새 인덱스에 alias를 추가하는 액션을 추가합니다.
    actions.append({"add": {"index": new_index_name, "alias": alias}})

    # 4. 모든 액션을 원자적으로 실행합니다.
    await es_async.indices.update_aliases(body={"actions": actions})

def _switch_single_alias_sync(new_index_name: str, alias: str):
    """(동기) 단일 alias를 새 인덱스로 원자적으로 전환합니다."""
    actions = []
    try:
        alias_response = es_sync.indices.get_alias(name=alias)
        current_indices = list(alias_response.keys())
        for index in current_indices:
            actions.append({"remove": {"index": index, "alias": alias}})
    except NotFoundError:
        logger.warning(f"Alias '{alias}' not found. It will be created on the new index '{new_index_name}'.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while getting alias '{alias}': {str(e)}")
        raise

    actions.append({"add": {"index": new_index_name, "alias": alias}})
    es_sync.indices.update_aliases(body={"actions": actions})


# --- 외부 호출용 메인 함수 ---

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def switch_aliases_to_new_index(new_index_name: str, aliases: List[str]):
    """
    주어진 alias 목록을 새 인덱스로 안전하게 전환합니다.
    이 함수는 Blue-Green 배포 전략의 핵심입니다

    Args:
        new_index_name: Alias를 연결할 새로운 인덱스의 이름.
        aliases: 전환할 alias의 리스트.
    """
    logger.info(f"Attempting to switch aliases {aliases} to new index '{new_index_name}'...")
    
    # 각 alias에 대해 전환 작업을 수행합니다.
    # update_aliases는 원자적이지만, for 루프 전체는 원자적이지 않습니다.
    # 하지만 각 alias 전환이 독립적이므로 이 방식이 더 명확하고 관리하기 좋습니다.
    for alias in aliases:
        if es_async:
            await _switch_single_alias_async(new_index_name, alias)
        else:
            _switch_single_alias_sync(new_index_name, alias)

    logger.info(f"Successfully switched aliases {aliases} to new index '{new_index_name}'.")

# --- 예시 사용법 (실제 호출 스크립트에서 사용) ---
# async def reindex_and_switch():
#     new_index = "my_new_index_name"
#     aliases_to_switch = [settings.ELASTICSEARCH_READ_ALIAS, settings.ELASTICSEARCH_WRITE_ALIAS]
#     # ... 여기에 new_index를 생성하고 데이터를 색인하는 로직 ...
#     await switch_aliases_to_new_index(new_index, aliases_to_switch)