import asyncio 
from elasticsearch import Elasticsearch, AsyncElasticsearch 

from app.core.config import settings 


# -------------------------------
# Elasticsearch 연결 관리
# -------------------------------

# 비동기 클라이언트 (FastAPI 비즈니스 로직용)
es_async = AsyncElasticsearch(
    hosts=[settings.ELASTICSEARCH_URL],
    basic_auth = (
        settings.ELASTIC_USERNAME,
        settings.ELASTIC_PASSWORD
    ) if settings.ELASTIC_USERNAME else None,
    verify_certs=False,
    request_timeout=30,
    max_retries=3,
    retry_on_timeout=True
)

# 동기 클라이언트(초기화 스크립트, 배치용)
es_sync = Elasticsearch(
    hosts=[settings.ELASTICSEARCH_URL],
    basic_auth=(
        settings.ELASTIC_USERNAME,
        settings.ELASTIC_PASSWORD
    ),
    verify_certs=False, 
    request_timeout=30,
    max_retries=3,
    retry_on_timeout=True
)

# 연결 테스트 함수 (웹 시작 시 호출)
async def check_es_connection():
    try:
        if await es_async.ping():
            print("[ES] Elasticsearch 연결 성공")
        else:
            print("[ES] 연결 실패 (Ping 응답 없음)")
    except Exception as e:
        print(f"[ES] 연결 오류: {e}")
    finally: 
        await es_async.close()


if __name__ == "__main__":
    asyncio.run(check_es_connection())    