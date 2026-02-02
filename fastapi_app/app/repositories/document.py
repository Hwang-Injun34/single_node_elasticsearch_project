from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession 

from app.models import Document, DocumentSegment

class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db 
    
    async def get_full_context_by_id(self, doc_id: int) -> Optional[Document]:
        """
        제목: 문서 전체 컨텍스트 조회
        목적: 문서 정보와 연결된 모든 세그먼트를 함께 반환
        핵심동작: joinedload로 Document.segments를 Eager Loading
        """
        stmt = (
            select(Document)
            # Document.segments (컬렉션)를 Eager Loading
            # 세그먼트를 순서대로 정렬하도록 명시(page_number -> id 순)
            .options(joinedload(Document.segments))
            .where(Document.id == doc_id)
        )

        result = await self.db.execute(stmt)
        return result.scalars().first()
    

    async def get_metadata_only_by_id(self, doc_id: int) -> Optional[Document]:
        """
        제목: 문서 메타데이터 조회
        목적: 세그먼트 없이 문서 기본 정보만 반환
        핵심동작: Document 단일 엔티티 조회
        """
        stmt = select(Document).where(Document.id == doc_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()