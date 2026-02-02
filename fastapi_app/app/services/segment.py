from typing import Optional

from app.repositories.segment import SegmentRepository
from app.models.document_segments import DocumentSegment


# ======================================================
# [제목] 문서 세그먼트 조회 서비스
# ------------------------------------------------------
# [목적]
#  - 세그먼트 ID를 기반으로 세그먼트와 부모 Document 정보를 함께 조회하여
#    API 계층에 전달한다.
#
# [핵심 동작]
#  - 문자열 형태의 segment_id를 정수로 변환
#  - Repository를 통해 Document 관계를 eager loading하여 조회
# ======================================================
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
