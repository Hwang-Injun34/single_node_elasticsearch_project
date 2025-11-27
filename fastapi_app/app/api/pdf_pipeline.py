from fastapi import APIRouter, Depends, BackgroundTasks

from app.services.pdf_pipeline.pdf_process import PdfProcessService
from app.dependencies.pdf_processing_pipeline import get_pdf_pipeline_service

from app.schema.crawler import CrawlerFilter

router = APIRouter()


@router.post("/run-extraction")
async def run_extraction(
    background_task: BackgroundTasks,
    pdf_service: PdfProcessService = Depends(get_pdf_pipeline_service)
):
    background_task.add_task()

    return 
