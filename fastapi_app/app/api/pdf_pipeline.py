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
    print(f"[API 요청] PDF 추출 시작(Limit: {limit})")
    await pdf_service.run_extraction(limit)
    return {"message": f"[1단계] 텍스트 추출 작업이 백그라운드에서 시작되었습니다. (Limit: {limit})"}


@router.post("/run-parser")
async def run_extraction(
    limit: int = Query(3, description="처리할 문서 개수"),
    pdf_service: PdfProcessService = Depends(get_pdf_pipeline_service)
):
    print(f"[API 요청] 세그먼트 파싱 시작(Limit: {limit})")
    await pdf_service.run_parser(limit)
    return {"message": f"[2단계] 세그먼트 파싱 작업이 백그라운드에서 시작되었습니다. (Limit: {limit})"}



@router.post("/run-track-a")
async def run_extraction(
    limit: int = Query(3, description="처리할 문서 개수"),
    pdf_service: PdfProcessService = Depends(get_pdf_pipeline_service)
):
    print(f"[API 요청] 키워드 추출 시작(Limit: {limit})")
    await pdf_service.run_track_a(limit)
    return {"message": f"[3-a단계] 키워드 추출 작업이 백그라운드에서 시작되었습니다. (Limit: {limit})"}



@router.post("/run-track-b")
async def run_extraction(
    limit: int = Query(3, description="처리할 문서 개수"),
    pdf_service: PdfProcessService = Depends(get_pdf_pipeline_service)
):
    print(f"[API 요청] 임베딩 벡터 생성 시작(Limit: {limit})")
    await pdf_service.run_track_b(limit)
    return {"message": f"[3-b단계] 임베딩 생성 작업이 백그라운드에서 시작되었습니다. (Limit: {limit})"}


@router.post("/run-all")
async def run_full_pipeline(
    background_task: BackgroundTasks, 
    limit: int = Query(3, description="처리할 문서 개수"),
    pdf_service: PdfProcessService = Depends(get_pdf_pipeline_service)
):
    background_task.add_task(pdf_service.run_full_pipeline, limit)
    return {"message": "전체 파이프라인 작업이 시작되었습니다."}