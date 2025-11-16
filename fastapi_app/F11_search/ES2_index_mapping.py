from app.F5_core.config import settings

# API 명세와 Pydantic 스키마에 맞춰 수정된 Elasticsearch 인덱스 매핑
INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 3,
        "number_of_replicas": 1,
        "analysis": {
            "tokenizer": {
                "korean_tokenizer": {
                    "type": "nori_tokenizer",
                    "decompound_mode": "mixed",
                    "user_dictionary": settings.ELASTICSEARCH_USER_DICT_PATH
                }
            },
            "filter": {
                "korean_stopwords": {
                    "type": "stop",
                    "stopwords_path": settings.ELASTICSEARCH_STOPWORDS_PATH
                },
                "korean_synonyms": {
                    "type": "synonym",
                    "synonyms_path": settings.ELASTICSEARCH_SYNONYMS_PATH,
                    "format": "solr"
                }
            },
            "analyzer": {
                "korean_analyzer": {
                    "type": "custom",
                    "tokenizer": "korean_tokenizer",
                    "filter": ["lowercase", "korean_stopwords", "korean_synonyms"]
                }
            }
        }
    },
    "mappings": {
        "dynamic": "strict",  # 정의되지 않은 필드는 허용하지 않음
        "properties": {
            # --- Core Identifiers ---
            "id": {"type": "keyword"},  # Feed.id 등 RDBMS의 PK, 고유 식별자
            "type": {"type": "keyword"}, # [수정] doc_type -> type. 콘텐츠 유형 ('정책', '보도자료' 등). 필터링에 사용

            # --- Searchable Text Fields (한국어 분석기 적용) ---
            # 참고: title 필드의 가중치(boost)는 매핑이 아닌 검색 쿼리에서 지정합니다.
            "title": {
                "type": "text",
                "analyzer": "korean_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"}  # 정확한 제목으로 정렬하거나 집계할 때 사용
                }
            },
            "summary": {
                "type": "text",
                "analyzer": "korean_analyzer"
            },
            "original_text": {
                "type": "text",
                "analyzer": "korean_analyzer"  # 본문 전체에 대한 깊은 검색용
            },
            # title, summary, original_text 등을 합친 통합 검색용 필드.
            # 데이터 인덱싱 시 이 필드를 채워주면, 검색 쿼리를 단순화할 수 있습니다.
            "content": {
                "type": "text",
                "analyzer": "korean_analyzer"
            },

            # --- Foreign Keys (내부 참조용) ---
            "organization_id": {"type": "integer"},
            "category_id": {"type": "integer"},
            
            # --- Filtering & Aggregation Fields ---
            "organization": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "keyword"},  # 'organizations' 필터 및 집계에 사용
                    "logo_url": {"type": "keyword", "index": False} # 검색 대상이 아니므로 인덱싱 제외
                }
            },
            # [추가] 카테고리 필터링, 집계, 정보 표시를 위해 추가
            "category": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "keyword"}  # 'categories' 필터 및 집계에 사용
                }
            },
            "tags": {"type": "keyword"},  # 태그 기반 필터링을 위한 필드

            # --- Sorting & Date Filtering Fields ---
            "published_date": {"type": "date"},  # 'date_from'/'date_to' 필터 및 'latest'/'oldest' 정렬에 사용
            "view_count": {"type": "integer"},     # 'views' 정렬에 사용
            "average_rating": {"type": "float"},    # [추가] 'rating' 정렬에 사용
            "bookmark_count": {"type": "integer"},  # [추가] API 응답 데이터에 포함
            
            # --- Retrieval-only Fields ---
            "url": {"type": "keyword", "index": False}, # [추가] 상세 페이지 URL. 검색 대상이 아니므로 인덱싱 제외
            "image_path": {"type": "keyword", "index": False}, # 검색 대상이 아닌 이미지 경로

            # --- General and Other Model Fields (통합 검색을 위한 확장성 필드) ---
            "metadata": {"type": "flattened"}, # 구조가 정해지지 않은 추가 정보 저장용
            "start_date": {"type": "date"},    # 이벤트/공고 등의 시작일
            "end_date": {"type": "date"},      # 이벤트/공고 등의 종료일
            "author": {"type": "keyword"},     # 작성자
            "preview": {"type": "text", "analyzer": "korean_analyzer"}, # 미리보기용 텍스트
            "display_order": {"type": "integer"}, # 특정 콘텐츠의 표시 순서
            
            # 'tags'와 유사하나, 다른 유형의 콘텐츠에서 사용할 수 있으므로 유지
            "tag": {"type": "keyword"} 
        }
    }
}