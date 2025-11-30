import asyncio 
from sqlalchemy import select 
from sqlalchemy.orm import selectinload

from elasticsearch import helpers

from app.dependencies.db import get_db
from app.models.document_segments import DocumentSegment

from app.search.connection import es_async, es_sync
from app.search.index_manager import INDEX_NAME

class MinutesIndexer: 
    def __init__(self):
        self.index_name = INDEX_NAME
    
    async def index_all_documents(self, batch_size: int=500):
        """
        [비동기] DB의 모든 세그먼트를 조회하여 ES에 색인 (Batch 처리)
        """
        print(f"[Indexer] 전체 데이터 색인 시작 (Batch: {batch_size})")

        async for db in get_db():
            # 임베딩이 완료된(벡터가 있는) 세그먼트만 조회
            # Document 정보도 함께 로딩(Join)
            offset = 0 
            total_indexed = 0 

            while True:
                # [Step 1] DB 조회 (Paging)
                stmt = (
                    select(DocumentSegment)
                    .options(selectinload(DocumentSegment.document)) # 부모 정보 로딩
                    .where(DocumentSegment.embedding_vector.isnot(None)) # 벡터 있는 것만
                    .limit(batch_size)
                    .offset(offset)
                )
                result = await db.execute(stmt)
                segments = result.scalars().all()

                if not segments:
                    break 

                # [Step 2] 데이터 변환(RDB -> ES JSON)
                actions = []
                for seg in segments:
                    doc = seg.document # 부모 문서

                    source = {
                        # --- 메타 데이터 ---
                        "doc_id": str(doc.id),
                        "title": doc.title,
                        "committee_name": doc.committeeName,
                        "conf_date": doc.confDate.isoformat() if doc.confDate else None,
                        "confer_num": doc.conferNum,
                        "pdf_link": doc.pdfLinkUrl,
                        
                        # --- 발언 데이터 ---
                        "segment_id": str(seg.id),
                        "page_number": seg.page_number,
                        "speaker_name": seg.speaker_name,
                        "speaker_role": seg.speaker_role,
                        
                        # --- 검색 데이터 ---
                        "content_text": seg.original_text,
                        "keywords": seg.keywords, # List[str]
                        "embedding_vector": seg.embedding_vector # List[float]
                    }

                    # Bulk Action 구조
                    action = {
                        "_index": self.index_name, 
                        "_id": str(seg.id), # 문서 ID는 세그먼트 ID로
                        "_source": source
                    }

                    actions.append(action)

                # [Step 3] Bulk Indexing (ES로 전송)
                if actions:
                    # async_bulk를 사용하여 비동기 전송
                    success_count, errors = await helpers.async_bulk(es_async, actions)
                    total_indexed += success_count 
                    print(f"   ✅ {success_count}건 색인 완료 (누적: {total_indexed})")

                    if errors:
                        print(f"   ⚠️ 오류 발생: {errors}")
                
                offset += batch_size 

            print(f"[Indexer] 전체 완료. 총 {total_indexed}건 색인됨.")

# 테스트용
if __name__ == "__main__":
    indexer = MinutesIndexer()
    asyncio.run(indexer.index_all_documents())