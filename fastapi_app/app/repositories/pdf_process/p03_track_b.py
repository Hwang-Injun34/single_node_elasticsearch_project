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
    
    async def get_segments_without_vector(self, limit: int):
        """
        [확실한 해결법]
        1. SQL NULL (진짜 없음)
        2. JSON 'null' (None이 JSON으로 잘못 들어간 경우)
        3. JSON [] (빈 리스트로 초기화된 경우)
        이 3가지를 모두 '처리 안 됨'으로 간주하고 조회합니다.
        """
        stmt = (
            select(DocumentSegment)
            .where(
                or_(
                    # 1. 진짜 SQL NULL인 경우 (가장 일반적)
                    DocumentSegment.embedding_vector.is_(None),
                    
                    # 2. JSON 데이터가 'null' 문자열로 들어간 경우 (MySQL 특성)
                    text("embedding_vector = 'null'"),
                    
                    # 3. 빈 리스트 [] 로 들어가 있는 경우 (길이가 0)
                    text("JSON_LENGTH(embedding_vector) = 0")
                )
            )
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update_vectors_bulk(self, data: List[dict]):
        """
        data = [{"id": 1, "embedding_vector": [...]}, ...]
        """
        await self.db.execute(
            update(DocumentSegment),
            data
        )
        await self.db.commit()
