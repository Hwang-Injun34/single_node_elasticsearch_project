from typing import List, Optional 


"""
제목: 하이브리드 검색 쿼리 빌더
목적: 키워드(BM25) + 벡터(K-NN) 기반 검색을 결합한 Elasticsearch 쿼리 생성
핵심동작: match 쿼리와 knn 쿼리를 가중치 기반으로 결합하고 필터와 하이라이트 옵션 적용
"""

def build_hybrid_query(
        keyword: str, 
        vector: List[float],
        committee: Optional[str] = None, 
        size: int = 20
) -> dict: 
    """
    [하이브리드 검색 쿼리 생성]
    1. 키워드 검색(BM25): content_text 필드
    2. 벡터 검색 (k-NN): embedding_vector 필드
    3. 필터링: 위원회, 위원
    """
    query = {
        # ===============================
        # 제목: 기본 검색 옵션
        # 목적: 결과 개수 제한 및 불필요한 필드 제외
        # 핵심동작: size 설정, embedding_vector 필드를 응답에서 제외
        # ===============================
        "size": size,
        "_source": {
            "excludes": ["embedding_vector"] # 결과에서 벡터는 뺌 (너무 길어서)
        },
        # ===============================
        # 제목: 키워드 기반 검색(BM25)
        # 목적: 텍스트 유사도를 기반으로 기본 랭킹 점수 산출
        # 핵심동작: content_text 필드에 match 쿼리를 적용하고 boost로 가중치 조절
        # ===============================
        "query": {
            "bool": {
                "must": [],
                "should": [
                    # A. 키워드 검색 (가중치 0.3)
                    {
                        "match": {
                            "content_text": {
                                "query": keyword,
                                "boost": 0.3
                            }
                        }
                    }
                ],
                "filter": []
            }
        },
        # ===============================
        # 제목: 벡터 기반 검색(k-NN)
        # 목적: 의미적 유사도를 기반으로 문서 후보군을 탐색
        # 핵심동작: embedding_vector 필드에 대해 cosine 유사도 기반 k-NN 검색 수행
        # ===============================
        "knn": {
            "field": "embedding_vector",
            "query_vector": vector,
            "k": size,
            "num_candidates": 100,
            "boost": 0.7
        }
    }

    # ===============================
    # 제목: 필터 조건 적용
    # 목적: 특정 위원회 데이터만 검색 결과에 포함
    # 핵심동작: bool.filter와 knn.filter에 동일한 term 필터 적용
    # ===============================
    if committee:
        query["query"]["bool"]["filter"].append(
            {"term": {"committee_name": committee}}
        )
        # k-NN에도 필터 적용 (8.x 기능)
        query["knn"]["filter"] = {"term": {"committee_name": committee}}

    # ===============================
    # 제목: 하이라이팅 설정
    # 목적: 검색어가 매칭된 본문 위치를 UI에서 강조 표시
    # 핵심동작: content_text 필드에 pre/post 태그를 지정하여 강조 영역 반환
    # ===============================
    query["highlight"] = {
        "fields": {
            "content_text": {
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            }
        }
    }

    return query