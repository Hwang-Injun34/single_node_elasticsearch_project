# Elasticsearch 클라이언트 모듈 가져오기
# - Elasticsearch: 동기 방식 클라이언트
# - AsyncElasticsearch: 비동기 방식 클라이언트

from elasticsearch import Elasticsearch, AsyncElasticsearch
from app.F5_core.config import settings

# ==========================
# 비동기 Elasticsearch 클라이언트 설정
# ==========================

# AsyncElasticsearch 인스턴스 생성
# 이 클라이언트는 asyncio 기반의 비동기 호출에 사용됨
es_async = AsyncElasticsearch(
    hosts=[settings.ELASTICSEARCH_URL], # Elasticsearch 서버의 URL 지정 (예: http://localhost:9201)
    http_auth=(                         # Elasticsearch 접속 인증 정보
        settings.ELASTICSEARCH_USERNAME, # 사용자 이름
        settings.ELASTICSEARCH_PASSWORD  # 비밀번호
    ),
    verify_certs=False,        # SSL 인증서 검증 활성화
    # True: 서버가 제공하는 SSL 인증서를 검증하여 신뢰할 수 있는지 확인
    # False: 인증서 검증을 하지 않음 (테스트 환경에서는 False로 쓰기도 함)
    ssl_show_warn=False       # SSL 관련 경고 메시지 비활성화
    # True면 인증서가 self-signed 등일 때 콘솔에 경고 출력
    # False면 SSL 관련 경고 메시지를 출력하지 않음
)


# ==========================
# 동기 Elasticsearch 클라이언트 설정
# ==========================

# Elasticsearch 인스턴스 생성
# 이 클라이언트는 blocking 방식의 동기 호출에 사용됨
es_sync = Elasticsearch(
    hosts=[settings.ELASTICSEARCH_URL],     # Elasticsearch 서버의 URL
    http_auth=(                    # Elasticsearch 접속 인증 정보
        settings.ELASTICSEARCH_USERNAME,  # 사용자 이름          
        settings.ELASTICSEARCH_PASSWORD   # 비밀번호
    ),
    verify_certs=False,          # SSL 인증서 검증 활성화
    ssl_show_warn=False         # SSL 관련 경고 메시지 비활성화
)
