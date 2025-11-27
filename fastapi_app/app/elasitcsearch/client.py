from elasticsearch import Elasticsearch, AsyncElasticsearch

from app.core.config import settings 

# ==========================
# 비동기 Elasticsearch 클라이언트 설정
# ==========================
es_async = AsyncElasticsearch(
    hosts=[settings.ELASTICSEARCH_HOST],
    http_auth = (
        settings.ELASTIC_USERNAME,
        settings.ELASTIC_PASSWORD
    ),
    verify_certs=False, 
    ssl_show_warn=False,
    timeout=30,
    max_retries=3,
    retry_on_timeout=True
)

# ==========================
# 동기 Elasticsearch 클라이언트 설정
# ==========================
es_sync = Elasticsearch(
    hosts=[settings.ELASTICSEARCH_HOST],
    http_auth=(
        settings.ELASTIC_USERNAME,
        settings.ELASTIC_PASSWORD
    ),
    verify_certs=False, 
    ssl_show_warn=False,
    timeout=30,
    max_retries=3,
    retry_on_timeout=True

)