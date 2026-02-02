import asyncio
from .p01_pdf_extraction import PdfExtractionService
from .p02_pdf_transcript_parser import PdfTranscriptParserService
from .p03_track_a import PdfKeywordExtractorService 
from .p03_track_b import PdfEmbeddingExtractorService

# ============================================================
# PDF 문서 처리 전체 파이프라인 오케스트레이터
# ------------------------------------------------------------
# [제목]
# PdfProcessService
#
# [목적]
# PDF → 텍스트 추출 → 발언 파싱 → 키워드 추출 → 임베딩 생성까지의
# 전체 문서 처리 흐름을 단계별로 조율하고 실행한다.
#
# [핵심 동작]
# - 단계별 서비스(P01~P03)를 순차 실행
# - 각 단계 실행 로그 출력
# - 전체 파이프라인 단일 진입점(run_full_pipeline) 제공
# ============================================================


class PdfProcessService: 
    def __init__(
        self,
        p01_service: PdfExtractionService,
        p02_service: PdfTranscriptParserService,
        p03_track_a_service: PdfKeywordExtractorService,
        p03_track_b_service: PdfEmbeddingExtractorService,
        
    ):
        self.p01_service = p01_service
        self.p02_service = p02_service 
        self.p03_track_a_service = p03_track_a_service
        self.p03_track_b_service = p03_track_b_service


    # ===============================
    #         [파이프라인]
    # ===============================

    # -------------------------------
    #          [1단계]
    # -------------------------------
    async def run_extraction(self, limit: int=3):
        print(f"[1단계] PDF 추출 시작 (Limit: {limit})")
        await self.p01_service.execute_pdf_extraction(limit)

    # -------------------------------
    #          [2단계]
    # -------------------------------
    async def run_parser(self, limit: int=3):
        print(f"[2단계] 파싱 및 세그먼트 분리 시작 (Limit: {limit})")
        await self.p02_service.segmentize_pages(limit)

    # -------------------------------
    #          [3-a단계]
    # -------------------------------
    async def run_track_a(self, limit: int=3):
        print(f"[3-a단계] 키워드 추출 시작 (Limit: {limit})")
        await self.p03_track_a_service.run_keyword_extraction(limit)

    # -------------------------------
    #          [3-b단계]
    # -------------------------------
    async def run_track_b(self, limit: int=3):
        print(f"[3-b단계] 임베딩 생성 시작 (Limit: {limit})")
        await self.p03_track_b_service.run_embedding_extraction()

    

    async def run_full_pipeline(self, limit: int):
        print("[전체 파이프라인] 시작")
        await self.run_extraction(limit)
        await self.run_parser(limit)
        await self.run_track_a(limit)
        await self.run_track_b(limit)
        print("[전체 파이프라인] 완료")
