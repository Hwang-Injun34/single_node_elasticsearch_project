import time 
from sentence_transformers import SentenceTransformer

from app.core.config import settings 

from app.search.connection import es_async
from app.search.index_manager import INDEX_NAME 
from app.search.query_builder import build_hybrid_query 

class SearchService:
    def __init__(self, model_instance: SentenceTransformer):
        self.model = model_instance

    async def search_minutes(self, keyword: str, committee: str = None, limit: int = 20):
        """
        사용자 검색어 -> 벡터 변환 -> ES 하이브리드 검색 -> 결과 반환
        """
        start_time = time.time()

        # 1. 검색어 벡터화 (Query Embedding)
        query_vector = self.model.encode(keyword).tolist()

        # 2. ES 쿼리 빌드 
        es_query = build_hybrid_query(keyword, query_vector, committee, limit)

        # 3. ES 검색 요청
        response = await es_async.search(index=INDEX_NAME, body=es_query)

        # 4. 결과 가공
        hits = response["hits"]["hits"]
        results = []

        for hit in hits:
            source = hit["_source"]
            score = hit["_score"]
            highlight = hit.get("highlight", {}).get("content_text", [source["content_text"][:200]])[0]

            results.append({
                "score": score,
                "segment_id": source["segment_id"],
                "doc_id": source["doc_id"],
                "title": source["title"],
                "content_text": source["content_text"],
                "highlight": highlight, # 하이라이트된 텍스트
                "speaker": f"{source['speaker_role']} {source['speaker_name']}",
                "committee_name": source["committee_name"],
                "conf_date": source["conf_date"],
                "keywords": source["keywords"]
            })

        duration = time.time() - start_time
        return {
            "total": response["hits"]["total"]["value"],
            "took": duration,
            "results": results
        }
