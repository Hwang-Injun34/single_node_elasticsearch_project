from fastapi import APIRouter, Depends, Path, HTTPException

from app.services.segment import SegmentService
from app.schema.integrated_data import SegmentDetail
from app.dependencies.segments import get_segment_service

router = APIRouter()

@router.get("/{segment_id}", response_model=SegmentDetail)
async def get_segment_detail(
    segment_id: str = Path(..., description="조회할 세그먼트의 고유 ID"),
    segment_service: SegmentService = Depends(get_segment_service)
): 
    """
    제목: 세그먼트 상세 조회 API
    목적: 특정 세그먼트의 메타데이터 및 내용 반환
    핵심동작: 세그먼트 조회 -> 없으면 404 -> 결과 반환
    """
    segment_data = await segment_service.get_segment_detail(segment_id)

    if not segment_data:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    return segment_data
