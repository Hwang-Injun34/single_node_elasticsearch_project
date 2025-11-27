from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db

from app.services.pdf_pipeline.pdf_process import PdfProcessService
from app.services.pdf_pipeline.p01_pdf_extraction import PdfExtractionService
from app.services.pdf_pipeline.p02_pdf_transcript_parser import PdfTranscriptParserService

from app.repositories.pdf_process.p01_pdf_extraction import PdfExtractionRepository
from app.repositories.pdf_process.p02_pdf_transcript_parser import PdfTranscriptParserRepository

# ===============================
# pdf 파이프라인 단계별 의존성 주입
# ===============================

# -- [1단계: pdf 추출] --
async def get_pdf_extraction_service(db: AsyncSession = Depends(get_db)) -> PdfExtractionService:
    return PdfExtractionService(PdfExtractionRepository(db))


# -- [2단계: 텍스트 발언 단위(segments) 파싱] --
async def get_pdf_transcript_parser_service(db: AsyncSession = Depends(get_db)) -> PdfTranscriptParserService:
    return PdfTranscriptParserService(PdfTranscriptParserRepository(db))



# -- [통합: PDF Data Pipeline Service Factory] --

async def get_pdf_pipeline_service(
    # [수정] Depends가 리턴하는 것은 'Service'이므로 타입 힌트도 Service여야 합니다.
    p01_service: PdfExtractionService = Depends(get_pdf_extraction_service),
    p02_service: PdfTranscriptParserService = Depends(get_pdf_transcript_parser_service)
) -> PdfProcessService:
    

    # 두 개의 하위 서비스를 통합 서비스에 주입
    return PdfProcessService(
        p01_service=p01_service, 
        p02_service=p02_service
    )