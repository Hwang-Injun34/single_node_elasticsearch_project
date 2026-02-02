from elasticsearch import Elasticsearch 
from app.search.connection import es_sync 


"""
제목: 회의록 검색용 Elasticsearch 인덱스 정의
목적: 회의록(Document + Segment) 데이터를 검색, 필터, 벡터 검색 가능하도록 구조화
핵심동작: 한국어 분석기 기반 매핑 정의 및 인덱스 생성/삭제 함수 제공
"""
INDEX_NAME = "minutes_v1"

"""
제목: 인덱스 매핑 및 설정 정의
목적: 한국어 형태소 분석(nori) 기반 텍스트 검색과 벡터 검색을 동시에 지원
핵심동작: analyzer, tokenizer, field 타입, dense_vector 설정 구성
"""
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
            # ===============================
            # 제목: [1] 메타데이터 필드(Document)
            # 목적: 문서 단위 필터링, 정렬, 식별에 사용
            # 핵심동작: keyword/date 타입으로 정확 매칭 및 범위 검색 지원
            # ===============================
            "doc_id": {"type":"keyword"},
            "title": {
                "type":"text",
                "analyzer": "korean_analyzer" # 제목 검색
            },
            "committee_name": {"type": "keyword"}, # 위원회(필터용)
            "conf_date": {"type": "date"}, # 날짜 (범위 검색)
            "confer_num": {"type": "keyword"}, # 회의 번호
            "pdf_link": {"type": "keyword", "index": False}, # 검색 제외, 링크용

            # ===============================
            # 제목: [2] 발언 데이터(Segment)
            # 목적: 발언자, 페이지 단위 필터링 및 그룹화 지원
            # 핵심동작: keyword/integer 타입으로 정확 매칭 처리
            # ===============================
            "segment_id": {"type": "keyword"}, # RDB Segment ID 
            "page_number": {"type": "integer"}, 
            "speaker_name": {"type": "keyword"}, # 발언자(필터용)
            "speaker_role": {"type": "keyword"}, # 직책

            # ===============================
            # 제목: [3] 본문 텍스트 검색 필드
            # 목적: 한국어 자연어 검색의 핵심 대상 텍스트 저장
            # 핵심동작: nori 기반 custom analyzer로 형태소 단위 검색 지원
            # ===============================
            "content_text":{
                "type":"text",
                "analyzer":"korean_analyzer"
            },
            "keywords": {"type": "keyword"}, # Track A 키워드 (태그용)
            
            # ===============================
            # 제목: [4] 임베딩 벡터 필드(Track B)
            # 목적: 의미 기반 유사도 검색(k-nn) 지원
            # 핵심동작: dense_vector + cosine similarity 기반 벡터 검색 활성화
            # ===============================
            "embedding_vector": {
                "type":"dense_vector",
                "dims": 768,            # SBERT 차원수
                "index": True,          # k-NN 검색 활성화
                "similarity": "cosine"  # 코사인 유사도
            }
        }
    }
}


def create_minutes_index():
    """
    제목: 회의록 인덱스 생성 함수
    목적: 인덱스가 없을 경우에만 안전하게 신규 생성
    핵심동작; 존재 여부 -> 없으면 INDEX_BODY 기반 생성
    """
    if es_sync.indices.exists(index=INDEX_NAME):
        print(f"인덱스 '{INDEX_NAME}'가 이미 존재합니다.")
        return 
    
    try:
        es_sync.indices.create(index=INDEX_NAME, body=INDEX_BODY)
        print(f"인덱스 '{INDEX_NAME}' 생성 완료!")
    except Exception as e:
        print(f"인덱스 생성 실패: {e}")

def delete_minutes_index():
    """
    제목: 회의록 인덱스 삭제 함수
    목적: 개발/재색인 시 기존 인덱스를 제거하기 위함
    핵심동작: 인덱스 존재 여부 확인 -> 있으면 삭제
    """
    if es_sync.indices.exists(index=INDEX_NAME):
        es_sync.indices.delete(index=INDEX_NAME)
        print(f"인덱스 '{INDEX_NAME}'삭제 완료")
    else:
        print(f"삭제할 인덱스 '{INDEX_NAME}'가 없음.")


# 테스트용
if __name__ == "__main__":
    create_minutes_index()
