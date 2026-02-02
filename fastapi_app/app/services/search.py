import time 
from sentence_transformers import SentenceTransformer

from app.core.config import settings 

from app.search.connection import es_async
from app.search.index_manager import INDEX_NAME 
from app.search.query_builder import build_hybrid_query 

# ======================================================
# [제목] 하이브리드 검색 서비스 (키워드 + 벡터 기반)
# ------------------------------------------------------
# [목적]
#  - 사용자의 자연어 검색어를 벡터로 변환한 뒤,
#    Elasticsearch 하이브리드 검색(BM25 + Vector Search)을 수행하여
#    회의록/문서 세그먼트 검색 결과를 반환한다.
#
# [핵심 동작]
#  - SentenceTransformer 모델을 이용해 검색어를 임베딩 벡터로 변환
#  - 키워드 검색 + 벡터 검색을 결합한 ES 쿼리 생성
#  - ES 응답을 API 응답 스키마에 맞게 가공 및 성능 로그 출력
# ======================================================


class SearchService:
    def __init__(self, model_instance: SentenceTransformer):
        self.model = model_instance

    async def search_minutes(self, keyword: str, committee: str = None, limit: int = 20):
        """
        사용자 검색어 -> 벡터 변환 -> ES 하이브리드 검색 -> 결과 반환
        """
        start_time = time.time()

        # 1. 검색어 벡터화 (여기가 시간이 꽤 걸릴 수 있음!)
        query_vector = self.model.encode(keyword).tolist()

        # 2. ES 쿼리 빌드 
        es_query = build_hybrid_query(keyword, query_vector, committee, limit)

        # 3. ES 검색 요청
        response = await es_async.search(index=INDEX_NAME, body=es_query)
        
        # ES 내부 연산 시간 (단위: ms)
        es_took_ms = response["took"]

        # 4. 결과 가공
        hits = response["hits"]["hits"]
        results = []

        for hit in hits:
            source = hit["_source"]
            score = hit["_score"]
            # highlight 처리 안전하게 (없을 경우 대비)
            highlight_field = hit.get("highlight", {}).get("content_text", [])
            highlight_text = highlight_field[0] if highlight_field else source["content_text"][:200]

            results.append({
                "score": score,
                "segment_id": source["segment_id"],
                "doc_id": source["doc_id"],
                "title": source["title"],
                "content_text": source["content_text"],
                "highlight": highlight_text,
                "speaker": f"{source['speaker_role']} {source['speaker_name']}",
                "committee_name": source["committee_name"],
                "conf_date": source["conf_date"],
                "keywords": source["keywords"]
            })

        # Python 총 소요 시간 (초 단위)
        total_duration_sec = time.time() - start_time
        
        # [로그 출력] 이렇게 찍어두면 디버깅할 때 범인 색출 가능
        print(f"[Perf] Total: {total_duration_sec:.4f}s | ES Took: {es_took_ms}ms")

        return {
            "total_hits": response["hits"]["total"]["value"],  # "total" -> "total_hits"
            "execution_time": total_duration_sec,
            "es_took": es_took_ms,  # "took" -> "es_took"
            "results": results
        }