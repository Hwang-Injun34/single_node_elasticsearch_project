from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from app.models.document_processes import DocumentProcess, ProcessStatus
from app.models.document_contents import DocumentContent

from app.schema.pdf import DocumentContentSaveSchema


# ===============================
# 1단계: PDF -> 텍스트 추출(PyMuPDF 기반)
# ===============================

class PdfExtractionRepository:
    def __init__(self, db_p01: AsyncSession):
        self.db = db_p01 
    
    async def commit(self):
        await self.db.commit()

    async def get_unprocessed_pdfs(self, limit: int):
        """
        아직 처리되지 않은(is_processed=False) 항목을 조회
        Document 정보를 함께 로딩(joinedload)하여 N+1 문제를 방지
        """
        stmt = (
            select(DocumentProcess)
            .options(joinedload(DocumentProcess.document))
            .where(DocumentProcess.status == ProcessStatus.PENDING)
            .limit(limit)
        )
        
        result = await self.db.scalars(stmt)
        return result.all()
    
    async def save_extraction_result(self, process_id: int, save_data: DocumentContentSaveSchema):
        """
        추출 결과를 DocumentContent 테이블에 저장(Insert)
        """

        content = DocumentContent(
            process_id=process_id, 
            compressed_page_texts = save_data.compressed_page_texts
        )
        await self.db.add(content)


    async def update_process_status(self, process_id: int, status: ProcessStatus):
        """
        DocumentProcess의 상태 업데이트
        """
        stmt = (
            update(DocumentProcess)
            .where(DocumentProcess.id == process_id)
            .values(status=status)
        )
        await self.db.execute(stmt)
        