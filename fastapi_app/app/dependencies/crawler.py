from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.services.crawler import NationalAssemblyCrawlerService
from app.repositories.crawler import NationalAssemblyCrawlerRepository

# -- 크롤링 --
async def get_crawl_service(db: AsyncSession = Depends(get_db)) -> NationalAssemblyCrawlerService:
    return NationalAssemblyCrawlerService(NationalAssemblyCrawlerRepository(db))