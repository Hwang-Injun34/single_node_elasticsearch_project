from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_, text
from sqlalchemy.orm import joinedload 

from typing import List 

from app.models.document_processes import DocumentProcess, ProcessStatus
from app.models.document_segments import DocumentSegment

# ===============================
# 3단계_TrackB: 임베딩 벡터 생성
# ===============================
class PdfEmbeddingExtractorRepository:
    def __init__(self, db_p03_track_b: AsyncSession):
        self.db = db_p03_track_b

    async def commit(self):
        await self.db.commit()

    async def get_segments_by_status(self):
        stmt = (
            select(DocumentProcess)
            .options(joinedload(DocumentProcess.segment))
            .where(DocumentProcess.status == ProcessStatus.KEYWORD)

        )
        
        result = await self.db.execute(stmt)
        return result.unique().scalars().all()
    
    
    async def update_vectors_bulk(self, data: List[dict]):
        """
        data = [{"id": 1, "embedding_vector": [...]}, ...]
        """
        await self.db.execute(
            update(DocumentSegment),
            data
        )
        await self.db.commit()
