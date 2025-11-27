import asyncio
from .p01_pdf_extraction import PdfExtractionService
from .p02_pdf_transcript_parser import PdfTranscriptParserService

from app.schema.pdf import PageTextSchema

class PdfProcessService: 
    def __init__(
        self,
        p01_service: PdfExtractionService,
        p02_service: PdfTranscriptParserService,  
    ):
        self.p01_service = p01_service
        self.p02_service = p02_service  

    # ===============================
    #       [파이프라인]
    # ===============================
    # 1단계
    # 1단계 -> 2단계 : process_id, pages_text_json
    # 2단계

    # 3단계 
    async def run_pdf_pipeline(self, ):
        # 1단계
        self.p01_service.execute_pdf_extraction(limit=3)


    async def execut_segmentation(self, process_id: int, pages_data: list[PageTextSchema]):
        # 1. 파싱 실행
        # 결과값은 DocumentPageSegmentsSchema 객체
        # segments_result = await self.p02_service.
        pass
