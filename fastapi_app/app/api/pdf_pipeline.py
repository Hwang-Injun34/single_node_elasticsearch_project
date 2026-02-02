from fastapi import APIRouter, Depends, BackgroundTasks, Query

from app.services.pdf_pipeline.pdf_process import PdfProcessService
from app.dependencies.pdf_processing_pipeline import get_pdf_pipeline_service

from app.schema.crawler import CrawlerFilter

router = APIRouter()


@router.post("/run-extraction")
async def run_extraction(
    limit: int = Query(3, description="처리할 문서 개수"),
    pdf_service: PdfProcessService = Depends(get_pdf_pipeline_service)
):  
    """
    제목: PDF 텍스트 추출 실행 API
    목적: 원본 PDF에서 텍스트 데이터를 추출
    핵심동작: 지정 개수만큼 문서를 처리하는 추출 파이프라인 실행
    """
    print(f"[API 요청] PDF 추출 시작(Limit: {limit})")
    await pdf_service.run_extraction(limit)
    return {"message": f"[1단계] 텍스트 추출 작업이 시작되었습니다. (Limit: {limit})"}


@router.post("/run-parser")
async def run_extraction(
    limit: int = Query(3, description="처리할 문서 개수"),
    pdf_service: PdfProcessService = Depends(get_pdf_pipeline_service)
):
    """
    제목: 세그먼트 파싱 실행 API 
    목적: 추출된 텍스트를 구조화된 세그먼트로 반환
    핵심동작: 문서 단위 파싱 파이프라인 실행
    """
    print(f"[API 요청] 세그먼트 파싱 시작(Limit: {limit})")
    await pdf_service.run_parser(limit)
    return {"message": f"[2단계] 세그먼트 파싱 작업이 시작되었습니다. (Limit: {limit})"}



@router.post("/run-track-a")
async def run_extraction(
    limit: int = Query(3, description="처리할 문서 개수"),
    pdf_service: PdfProcessService = Depends(get_pdf_pipeline_service)
):
    """
    제목: 키워드 추출 실행 API 
    목적: 세그먼트 기반 핵심 키워드 데이터 생성
    핵심동작: Track-A 처리 파이프라인 실행
    """
    print(f"[API 요청] 키워드 추출 시작(Limit: {limit})")
    await pdf_service.run_track_a(limit)
    return {"message": f"[3-a단계] 키워드 추출 작업이 시작되었습니다. (Limit: {limit})"}



@router.post("/run-track-b")
async def run_extraction(
    pdf_service: PdfProcessService = Depends(get_pdf_pipeline_service)
):
    """
    제목: 임베딩 생성 실행 API 
    목적: 문서/세그먼트 벡터 임베딩 생성
    핵심동작: Track-B 파이프라인 실행
    """
    print(f"[API 요청] 임베딩 벡터 생성 시작")
    await pdf_service.run_track_b()
    return {"message": f"[3-b단계] 임베딩 생성 작업이시작되었습니"}


@router.post("/run-all")
async def run_full_pipeline(
    background_task: BackgroundTasks, 
    limit: int = Query(3, description="처리할 문서 개수"),
    pdf_service: PdfProcessService = Depends(get_pdf_pipeline_service)
):
    """
    제목: 전체 PDF 처리 파이프라인 실행 API 
    목적: 추출 -> 파싱 -> 키워드 -> 임베딩 전체 단계 자동 수행
    핵심동작: 백그라운드 태스크로 전체 파이프라인 실행
    """
    background_task.add_task(pdf_service.run_full_pipeline, limit)
    return {"message": "전체 파이프라인 작업이 시작되었습니다."}