import os
from elasticsearch import Elasticsearch, NotFoundError
from dotenv import load_dotenv

# --- 환경 변수 로드 ---
# 이 파일은 main.py의 startup 이벤트에서 호출되므로, 
# main.py에서 load_dotenv()가 이미 실행되었다고 가정합니다.

# --- 설정값 가져오기 ---
# F5_core.config 에서 직접 가져오는 것이 더 안정적입니다.
# 하지만 순환 참조(circular import) 문제가 발생할 수 있으므로, os.getenv를 유지합니다.
ES_URL = os.getenv("ELASTICSEARCH_URL")
ES_USER = os.getenv("ELASTICSEARCH_USERNAME")
ES_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
INDEX_PREFIX = os.getenv("ELASTICSEARCH_INDEX_PREFIX", "content_index")
READ_ALIAS = os.getenv("ELASTICSEARCH_READ_ALIAS", "content_search")
WRITE_ALIAS = os.getenv("ELASTICSEARCH_WRITE_ALIAS", "content_write")

# --- 사용자 정의 분석기 및 인덱스 매핑 ---
# 사용자님의 코드에서 가져온 완벽한 인덱스 설계도입니다.
INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 3,
        "number_of_replicas": 1,
        "analysis": {
            "tokenizer": {
                "korean_tokenizer": {
                    "type": "nori_tokenizer",
                    "decompound_mode": "mixed",
                    # Dockerfile.elasticsearch에서 설정된 경로를 사용합니다.
                    "user_dictionary": "user_dictionary/userdict_ko.txt"
                }
            },
            "filter": {
                "korean_stopwords": {
                    "type": "stop",
                    # Dockerfile.elasticsearch에서 설정된 경로를 사용합니다.
                    "stopwords_path": "user_dictionary/stopwords.txt"
                },
                "korean_synonyms": {
                    "type": "synonym",
                    # Dockerfile.elasticsearch에서 설정된 경로를 사용합니다.
                    "synonyms_path": "user_dictionary/synonym-set.txt",
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
        "dynamic": "strict",
        "properties": {
            "id": {"type": "keyword"},
            "type": {"type": "keyword"},
            "title": {
                "type": "text", "analyzer": "korean_analyzer",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "summary": {"type": "text", "analyzer": "korean_analyzer"},
            "original_text": {"type": "text", "analyzer": "korean_analyzer"},
            "content": {"type": "text", "analyzer": "korean_analyzer"},
            "organization_id": {"type": "integer"},
            "category_id": {"type": "integer"},
            "organization": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "keyword"},
                    "logo_url": {"type": "keyword", "index": False}
                }
            },
            "category": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "keyword"}
                }
            },
            "tags": {"type": "keyword"},
            "published_date": {"type": "date"},
            "view_count": {"type": "integer"},
            "average_rating": {"type": "float"},
            "bookmark_count": {"type": "integer"},
            "url": {"type": "keyword", "index": False},
            "image_path": {"type": "keyword", "index": False},
            "metadata": {"type": "flattened"},
            "start_date": {"type": "date"},
            "end_date": {"type": "date"},
            "author": {"type": "keyword"},
            "preview": {"type": "text", "analyzer": "korean_analyzer"},
            "display_order": {"type": "integer"},
            "tag": {"type": "keyword"} 
        }
    }
}


def initialize_elasticsearch():
    """Elasticsearch에 연결하고, 인덱스 템플릿과 초기 인덱스를 설정합니다."""
    print("--- Starting Elasticsearch Initialization ---")
    try:
        es = Elasticsearch(ES_URL, basic_auth=(ES_USER, ES_PASSWORD))
        if not es.ping():
            print("[ERROR] Elasticsearch connection failed!")
            return
        print("[SUCCESS] Elasticsearch connection successful!")

        # 1. Kibana에서 ILM 정책('auto_delete_3_days')이 생성되었는지 확인
        try:
            es.ilm.get_lifecycle(policy="auto_delete_3_days")
            print("[INFO] ILM policy 'auto_delete_3_days' found.")
            ilm_policy_name = "auto_delete_3_days"
        except NotFoundError:
            print("[WARNING] ILM policy 'auto_delete_3_days' not found in Kibana. ILM will not be applied.")
            ilm_policy_name = None

        # 2. 인덱스 템플릿 생성 또는 업데이트
        template_name = f"{INDEX_PREFIX}_template"
        template_body = {
            "index_patterns": [f"{INDEX_PREFIX}-*"],
            "template": INDEX_MAPPING,
        }
        # ILM 정책이 존재하면 템플릿에 추가
        if ilm_policy_name:
            template_body["template"]["settings"]["index.lifecycle.name"] = ilm_policy_name
        
        es.indices.put_template(name=template_name, body=template_body)
        print(f"[SUCCESS] Index template '{template_name}' created/updated.")
        if ilm_policy_name:
            print(f"    - ILM policy '{ilm_policy_name}' applied.")

        # 3. 쓰기 별칭(write alias)이 없으면, 첫 번째 인덱스 및 별칭 생성
        if not es.indices.exists_alias(name=WRITE_ALIAS):
            print(f"[INFO] Write alias '{WRITE_ALIAS}' not found. Creating initial index and aliases...")
            initial_index_name = f"{INDEX_PREFIX}-000001"
            
            # 템플릿이 적용되도록 인덱스 생성
            es.indices.create(index=initial_index_name)
            print(f"[SUCCESS] Initial index '{initial_index_name}' created.")

            # 쓰기 및 읽기 별칭 설정
            es.indices.put_alias(index=initial_index_name, name=WRITE_ALIAS)
            es.indices.put_alias(index=initial_index_name, name=READ_ALIAS)
            print(f"[SUCCESS] Aliases '{WRITE_ALIAS}' and '{READ_ALIAS}' created for the initial index.")
        else:
            print(f"[INFO] Write alias '{WRITE_ALIAS}' already exists. Skipping initial index creation.")

    except Exception as e:
        print(f"[ERROR] An error occurred during Elasticsearch initialization: {e}")
    finally:
        print("--- Elasticsearch Initialization Finished ---")