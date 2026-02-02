from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from app.models.document_processes import DocumentProcess, ProcessStatus
from app.models.document_contents import DocumentContent

from app.schema.pdf import DocumentContentSaveSchema


# ===============================
# 1단계: PDF -> 텍스트 추출
# ===============================

class PdfExtractionRepository:
    def __init__(self, db_p01: AsyncSession):
        self.db = db_p01 
    
    async def commit(self):
        """ 
        제목: 트랜잭션 커밋
        목적: 현재 세션 변경 사항 DB 반영
        핵심동작: commit() 호출
        """
        await self.db.commit()

    async def get_unprocessed_pdfs_by_status(self, limit: int):
        """
        제목: 미처리 PDF 조회
        목적: 아직 처리되지 않은 문서 목록 조회
        핵심동작: PENDING 상태 DocumentProcess 조회(Document join)
        """
        stmt = (
            select(DocumentProcess)
            .options(joinedload(DocumentProcess.document))
            .where(DocumentProcess.status == ProcessStatus.PENDING)
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def save_extraction_result(self, process_id: int, save_data: DocumentContentSaveSchema):
        """
        제목: 추출 결과 저장
        목적: PDF에서 추출한 텍스트 데이터를 DB에 저장
        핵심동작: DocumentContent INSERT
        """

        content = DocumentContent(
            process_id=process_id, 
            compressed_page_texts = save_data.compressed_page_texts
        )
        self.db.add(content)


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
        