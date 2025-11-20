from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import BIGINT
from datetime import datetime
from app.database.connection import Base

class CrawlIndex(Base):
    __tablename__ = "crawl_index"

    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    unique_hash = Column(String(64), unique=True, nullable=False)
    source_url = Column(String(500), nullable=True)
    report_id = Column(BIGINT(unsigned=True), ForeignKey("reports.report_id"), nullable=True, index=True)
    crawled_at = Column(DateTime, default=datetime.utcnow)
    