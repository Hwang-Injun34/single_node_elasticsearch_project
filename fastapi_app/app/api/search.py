from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.services.search import SearchService
from app.dependencies.search import get_search_service
from app.schema.search import SearchResponse
router = APIRouter()

# 리턴 메시지 모두 수정할 것

@router.get("/", response_model=SearchResponse)
async def search_minutes(
    q: str = Query(..., description="검색어"),
    committee: Optional[str] = Query(None, description="위원회 필터"),
    limit: int = 20, 
    service: SearchService = Depends(get_search_service)
):
    """
    국회 회의록 하이브리드 검색 API
    """
    result = await service.search_minutes(q, committee, limit)
    return result 
    
