from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.services.segment import SegmentService
from app.repositories.segment import SegmentRepository 

async def get_segment_service(db: AsyncSession = Depends(get_db)) -> SegmentService:
    return SegmentService(SegmentRepository(db))


