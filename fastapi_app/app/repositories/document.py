from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession 

from app.models import Document, DocumentSegment

class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db 
    
    async def get_full_context_by_id(self, doc_id: str) -> Optional[Document]:
        """
        Document ID를 기반으로 문서 정보와 연결된 모든 세그먼트 정보를 Eager Loading하여 반환
        """
        stmt = (
            select(Document)
            # Document.segments (컬렉션)를 Eager Loading
            # 세그먼트를 순서대로 정렬하도록 명시(page_number -> id 순)
            .options(selectinload(Document.segments)
            )
            .where(Document.id == doc_id)
        )

        result = await self.db.execute(stmt)
        return result.scalars().unique().first()