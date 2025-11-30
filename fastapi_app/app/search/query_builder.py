from typing import List, Optional 

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
        "size": size,
        "_source": {
            "excludes": ["embedding_vector"] # 결과에서 벡터는 뺌 (너무 길어서)
        },
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
        # B. 벡터 검색 (k-NN) (가중치 0.7)
        "knn": {
            "field": "embedding_vector",
            "query_vector": vector,
            "k": size,
            "num_candidates": 100,
            "boost": 0.7
        }
    }

    # 2. 필터 추가 (위원회 등)
    if committee:
        query["query"]["bool"]["filter"].append(
            {"term": {"committee_name": committee}}
        )
        # k-NN에도 필터 적용 (8.x 기능)
        query["knn"]["filter"] = {"term": {"committee_name": committee}}

    # 3. 하이라이팅 (검색어가 어디 있는지 표시)
    query["highlight"] = {
        "fields": {
            "content_text": {
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            }
        }
    }

    return query