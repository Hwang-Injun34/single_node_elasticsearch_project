from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search import SearchService

async def get_search_service():
    return SearchService