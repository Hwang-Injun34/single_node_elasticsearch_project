import hashlib 
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select

from app.models.crawler_index import CrawlIndex
from app.models.report_eras import ReportEra 
from app.models.reports import Report

class CrawlerRepositoryKSH:
    def __init__(self, db: AsyncSession):
        self.db = db 
    
    # -- 중복 체크 --
    async def is_crawled(self, doc_id: str) -> bool:
        unique_has = hashlib.sha256(doc_id.encode()).hexdigest()
        stmt = select(CrawlIndex).where(
            CrawlIndex.unique_hash == unique_has
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
    

    # -- CrawlIndex 저장 --
    async def save_crawl_index(self, doc_id: str, source_url: str, report_id: int):
        unique_has = hashlib.sha256(doc_id.encode()).hexdigest()

        crawl_index = CrawlIndex(
            unique_has=unique_has,
            source_url=source_url,
            report_id = report_id
        )
        self.db.add(crawl_index)
        await self.db.commit()

    
    # -- Report 저장 -- 
    async def save_report(self, report_data: dict) -> int:
        report = Report(**report_data)
        self.db.add(report)
        await self.db.commit()
        return report.report_id 
    

    # -- ReportEra 저장 --
    async def save_report_era(self, era_data: dict):
        report_era = ReportEra(**era_data)
        self.db.add(report_era)
        await self.db.commit()
        