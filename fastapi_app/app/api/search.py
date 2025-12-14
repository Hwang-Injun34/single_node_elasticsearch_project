from fastapi import APIRouter, Depends, Query
from typing import Optional
import time  # ✅ [필수] 시간 측정을 위해 추가

from app.services.search import SearchService
from app.dependencies.search import get_search_service
from app.schema.search import SearchResponse

router = APIRouter()

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
    # ✅ [1] 시작 시간 기록
    start_time = time.time()
    
    # 서비스 로직 실행
    result = await service.search_minutes(q, committee, limit)
    
    # ✅ [2] 종료 시간 기록 및 계산
    end_time = time.time()
    duration = end_time - start_time
    
    if isinstance(result, dict):
        hit_count = result.get('total_hits', 0)
    else:
        hit_count = getattr(result, 'total_hits', 'Unknown')

    print(f"\n📊 [Total Latency] 전체 소요 시간")
    print(f" - 검색어    : '{q}'")
    print(f" - 소요 시간 : {duration:.4f} sec")
    print(f" - 결과 건수 : {hit_count}") 
    return result