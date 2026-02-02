import asyncio 
from elasticsearch import Elasticsearch, AsyncElasticsearch 

from app.core.config import settings 


# -------------------------------
# Elasticsearch 연결 관리
# -------------------------------

""" 
제목: 비동기 Elasticsearch 클라이언트
목적: FastAPI 요청 처리 등 런타임 비즈니스 로직에서 사용
핵심동작: 인증/타임아웃/재시도 옵션 설정
"""
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

""" 
제목: 동기 Elasticsearch 클라이언트
목적: 초기화 스크립트, 배치 작업 등 동기 컨텍스트에서 사용
핵심동작: 비동기 클라이언트와 동일 설정으로 연결 생성
"""
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

""" 
제목: Elasticsearch 연결 테스트 함수
목적: 애플리케이션 시작 시 ES 연결 상태를 검증
핵심동작: ping 호출 후 성공/실패 로그 출력 및 연결 종료
"""
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