from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional

from app.models import DocumentSegment



class SegmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db 

    async def get_by_id_with_document(self, segment_id: int) -> Optional[DocumentSegment]:
        """
        Segment ID를 기반으로 Segment와 부모 Document를 Eager Loading하여 ORM 객체를 반환
        """
        stmt = (
            select(DocumentSegment)
            .options(selectinload(DocumentSegment.document))
            .where(DocumentSegment.id == segment_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    