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
        제목: 세그먼트 단건 조회(Document 포함)
        목적: 세그먼트 정보와 부모 Document를 함께 반환
        핵심동작: selectionload로 Document 관계 로딩
        """
        stmt = (
            select(DocumentSegment)
            .options(selectinload(DocumentSegment.document))
            .where(DocumentSegment.id == segment_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    