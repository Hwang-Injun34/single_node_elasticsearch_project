from fastapi import APIRouter, Depends

from app.services.crawler import NationalAssemblyCrawlerService
from app.dependencies.crawler import get_crawl_service
from app.schema.crawler import CrawlerFilter

router = APIRouter()

@router.get('/test')
async def get_national_assembly_crawler(
    filters: CrawlerFilter,
    crawler_service: NationalAssemblyCrawlerService = Depends(get_crawl_service)
):  
    result = await crawler_service.na_crawl(filters)
    return result
