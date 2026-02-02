from fastapi import APIRouter, Depends

from app.services.crawler import NationalAssemblyCrawlerService
from app.dependencies.crawler import get_crawl_service
from app.schema.crawler import CrawlerFilter

router = APIRouter()

@router.post('/national-assembly')
async def national_assembly_crawler(
    filters: CrawlerFilter,
    crawler_service: NationalAssemblyCrawlerService = Depends(get_crawl_service)
):  
    """
    제목: 국회 회의록 크롤링 실행 API
    목적: 조건에 맞는 국회 회의록 데이터를 수집
    핵심동작: 필터 전달 -> 크롤러 서비스 실행 -> 결과 반환
    """
    result = await crawler_service.na_crawl(filters)
    return result
