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
        """ 
        제목: 트랜잭션 커밋
        목적: 현재 세션 변경 사항 DB 반영
        핵심동작: commit() 호출
        """
        await self.db.commit()

    async def get_segments_by_status(self):
        """ 
        제목: 임베딩 대상 세그먼트 조회
        목적: KEYWORD 단계가 완료된 문서 세그먼트를 가져온다
        핵심동작: DocumentProcess + segment join 조회
        """
        stmt = (
            select(DocumentProcess)
            .options(joinedload(DocumentProcess.segment))
            .where(DocumentProcess.status == ProcessStatus.KEYWORD)

        )
        
        result = await self.db.execute(stmt)
        return result.unique().scalars().all()
    
    
    async def update_vectors_bulk(self, data: List[dict]):
        """
        제목: 임베딩 벡터 일괄 저장
        목적: 생성된 임베딩 벡터를 세그먼트에 반영
        핵심동작: SQLAlchemy bulk update 실행
        """
        await self.db.execute(
            update(DocumentSegment),
            data
        )
        await self.db.commit()
