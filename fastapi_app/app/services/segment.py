from typing import Optional

from app.repositories.segment import SegmentRepository
from app.models.document_segments import DocumentSegment

class SegmentService:
    def __init__(self, repo: SegmentRepository):
        self.db_repo = repo
    
    async def get_segment_detail(self, segment_id: str) -> Optional[DocumentSegment]:
        """
        [비즈니스 로직]: 데이터베이스에서 세그먼트를 조회하고, 필요 시 가공 로직 수행
        """
        int_id = int(segment_id)
        segment = await self.db_repo.get_by_id_with_document(int_id)

        return segment
