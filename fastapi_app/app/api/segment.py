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
    segment_data = await segment_service.get_segment_detail(segment_id)

    if not segment_data:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    return segment_data
