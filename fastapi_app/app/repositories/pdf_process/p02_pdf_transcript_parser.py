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
        """ 
        제목: 트랜잭션 커밋
        목적: 현재 세션 변경 사항 DB 반영
        핵심동작: commit() 호출
        """
        await self.db.commit()

    async def get_text_by_status(self, limit: int):
        """
        제목: 파싱 대상 텍스트 조회
        목적: 추출 완료(EXTRACTED) 상태 문서 조회
        핵심동작: DocumentProcess + Content join 조회
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
        제목: 세그먼트 파싱 결과 저장
        목적: 기존 DocumentContent에 화자/문단 세그먼트 결과 업데이트
        핵심동작: speaker_segments 컬러 UPDATE
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