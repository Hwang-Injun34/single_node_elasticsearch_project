from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from app.models.document_contents import DocumentContent
from app.models.document_processes import DocumentProcess, ProcessStatus
from app.schema.pdf import DocumentPageSegmentsSchema

# ===============================
# 2단계: segments 분리 
# ===============================

class PdfTranscriptParserRepository:
    def __init__(self, db_p02: AsyncSession):
        self.db = db_p02

    async def commit(self):
        await self.db.commit()

    async def get_unprocessed_pdfs(self, limit: int):
        """
        아직 처리되지 않은(is_processed=False) 항목을 조회
        Document 정보를 함께 로딩(joinedload)하여 N+1 문제를 방지
        """
        stmt = (
            select(DocumentProcess)
            .options(joinedload(DocumentProcess.content))
            .where(DocumentProcess.status == ProcessStatus.EXTRACTED)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()


    async def save_transcript_parser_result(self, process_id: int, result_segments: DocumentPageSegmentsSchema):
        """
        이미 존재하는 DocumentContent row의 document_segment_json 컬럼을 업데이트
        """
        json_data = result_segments.model_dump()

        stmt = (
            update(DocumentContent)
            .where(DocumentContent.process_id == process_id)
            .values(speaker_segments=json_data)
        )

        await self.db.execute(stmt)


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