# app/scripts/reindex.py

import asyncio
import logging

# ✨ 1. DB 세션을 가져오는 제너레이터 함수를 import 합니다.
#    get_db 함수는 FastAPI 의존성 주입을 위한 것이지만,
#    스크립트에서도 동일한 패턴으로 사용할 수 있습니다.
from app.F8_database.session import get_db

# ✨ 2. 재색인 메인 함수를 import 합니다.
from app.F11_search.ES6_indexer import run_reindexing

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """
    재색인 프로세스를 실행하는 메인 비동기 함수
    """
    logger.info("Starting Elasticsearch re-indexing process...")
    
    # ✨ 3. get_db() 제너레이터를 사용하여 DB 세션을 생성합니다.
    #    async for ... in get_db() 패턴을 사용하면,
    #    try/finally 블록 없이도 세션이 안전하게 닫힙니다.
    db_session_generator = get_db()
    
    try:
        # 제너레이터에서 첫 번째(그리고 유일한) 세션 객체를 가져옵니다.
        session = await db_session_generator.__anext__()
        
        # 가져온 세션을 사용하여 재색인 함수를 실행합니다.
        await run_reindexing(session)
        
        logger.info("Re-indexing process completed successfully.")

    except Exception as e:
        logger.error(f"Re-indexing process failed: {e}", exc_info=True)
        # 실패 시 명시적으로 제너레이터를 닫아줍니다. (선택사항, 안전장치)
        await db_session_generator.aclose()
        
    finally:
        # 성공/실패 여부와 관계없이 세션 제너레이터의 나머지 부분을 실행하여
        # commit 또는 rollback을 수행하고 세션을 닫습니다.
        try:
            await db_session_generator.__anext__()
        except StopAsyncIteration:
            # 제너레이터가 정상적으로 끝났음을 의미합니다.
            pass

if __name__ == "__main__":
    # 비동기 메인 함수 실행
    asyncio.run(main())