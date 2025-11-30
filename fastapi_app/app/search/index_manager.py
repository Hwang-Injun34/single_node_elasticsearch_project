from elasticsearch import Elasticsearch 
from app.search.connection import es_sync 

INDEX_NAME = "minutes_v1"

# --------------------------
# 인덱스 매핑 (Mapping) 정의
# --------------------------
INDEX_BODY = {
    "settings": {
        "nubmer_of_shards:": 1, 
        "number_of_replicas": 0, # 단일 노드이므로 0
        "analysis": {
            "tokenizer": {
                "nori_tokenizer_mixed": {
                    "type": "nori_tokenizer",
                    "decompound_mode": "mixed" # 복합명사 분해(예: 삼성전자 -> 삼성, 전자, 삼성전자)
                }
            },
            "analyzer": {
                "korean_analyzer": {
                    "type":"custom",
                    "tokenizer": "nori_tokenizer_mixed",
                    "filter": ["lowercase", "nori_readingform", "stop"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            # --- 1. 메타 데이터 (Document) --- 
            "doc_id": {"type":"keyword"},
            "title": {
                "type":"text",
                "analyzer": "korean_analyzer" # 제목 검색
            },
            "committee_name": {"type": "keyword"}, # 위원회(필터용)
            "conf_date": {"type": "date"}, # 날짜 (범위 검색)
            "confer_num": {"type": "keyword"}, # 회의 번호
            "pdf_link": {"type": "keyword", "index": False}, # 검색 제외, 링크용


            # --- 2. 발언 데이터 (Segment) ---
            "segment_id": {"type": "keyword"}, # RDB Segment ID 
            "page_number": {"type": "integer"}, 
            "speaker_name": {"type": "keyword"}, # 발언자(필터용)
            "speaker_role": {"type": "keyword"}, # 직책

            # --- 3. 본문 텍스트 (검색 핵심) ---
            "content_text":{
                "type":"text",
                "analyzer":"korean_analyzer"
            },
            "keywords": {"type": "keyword"}, # Track A 키워드 (태그용)
            
            # --- 4. 벡터 데이터 (Track B) ---
            "embedding_vector": {
                "type":"dense_vector",
                "dims": 768,            # SBERT 차원수
                "index": True,          # k-NN 검색 활성화
                "similarity": "cosine"  # 코사인 유사도
            }
        }
    }
}

# --------------------------
# 인덱스 관리 함수
# --------------------------
def create_minutes_index():
    """ 인덱스 생성(이미 있으면 건너뜀) """
    if es_sync.indices.exists(index=INDEX_NAME):
        print(f"ℹ️ 인덱스 '{INDEX_NAME}'가 이미 존재합니다.")
        return 
    
    try:
        es_sync.indices.create(index=INDEX_NAME, body=INDEX_BODY)
        print(f"✅ 인덱스 '{INDEX_NAME}' 생성 완료!")
    except Exception as e:
        print(f"❌ 인덱스 생성 실패: {e}")

def delete_minutes_index():
    """ 인덱스 삭제 """
    if es_sync.indices.exists(index=INDEX_NAME):
        es_sync.indices.delete(index=INDEX_NAME)
        print(f"인덱스 '{INDEX_NAME}'삭제 완료")
    else:
        print(f"삭제할 인덱스 '{INDEX_NAME}'가 없음.")


# 테스트용
if __name__ == "__main__":
    create_minutes_index()
