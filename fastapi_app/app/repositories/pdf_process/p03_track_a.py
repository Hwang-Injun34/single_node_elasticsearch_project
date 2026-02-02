
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession 
from typing import List

from app.models.document_processes import DocumentProcess, ProcessStatus
from app.models.document_segments import DocumentSegment
from app.schema.pdf import DocumentSegmentSaveSchema

# ===============================
# 3단계_TrackA: 키워드 추출
# ===============================
class PdfKeywordExtractorRepository:
    def __init__(self, db_p03_track_a: AsyncSession):
        self.db = db_p03_track_a

    async def commit(self):
        """ 
        제목: 트랜잭션 커밋
        목적: 현재 세션 변경 사항 DB 반영
        핵심동작: commit() 호출
        """
        await self.db.commit()

    async def get_speaker_texts(self, limit: int):
        """
        제목: 키워드 추출 대상 조회
        목적: PARSED 상태 문서의 발화 텍스트 조회
        핵심동작: DocumentProcess + Content join 조회
        """
        stmt = (
            select(DocumentProcess)
            .options(joinedload(DocumentProcess.content))
            .where(DocumentProcess.status == ProcessStatus.PARSED)
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def save_keyword_result(self, document_id: int, save_dtos: List[DocumentSegmentSaveSchema]):
        """
        제목: 키워드 추출 결과 저장
        목적: 문서 세그먼트 단위 키워드 데이터 저장
        핵심동작: 기존 데이터 삭제 -> Bulk Insert
        """
        # 1. 기존 데이터 삭제
        delete_stmt = delete(DocumentSegment).where(DocumentSegment.document_id == document_id)
        await self.db.execute(delete_stmt)

        # 2. DTO -> Model 변환
        segment_to_add = [
            DocumentSegment(
                document_id=dto.document_id,
                process_id=dto.process_id,
                page_number=dto.page_number,
                speaker_name=dto.speaker_name,
                speaker_role=dto.speaker_role,
                original_text=dto.original_text,
                keywords=dto.keywords,
                embedding_vector=None 
            )
            for dto in save_dtos
        ]
        
        # 3. 일괄 추가(Bulk Insert)
        self.db.add_all(segment_to_add)


    async def update_process_status(self, process_id: int, status: ProcessStatus):
        """
        제목: 처리 상태 업데이트
        목적: DocumentProcess 상태 변경 관리
        핵심동작: status 컬럼 UPDATE
        """
        stmt = (
            update(DocumentProcess)
            .where(DocumentProcess.id == process_id)
            .values(status=status)
        )
        await self.db.execute(stmt)
