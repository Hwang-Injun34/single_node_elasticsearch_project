import pytest
import asyncio
from unittest.mock import MagicMock

from app.services.pdf_pipeline.p03_track_a import PdfKeywordExtractorService
from app.schema.pdf import DocumentPageSegmentsSchema, DocumentSegmentSaveSchema
from app.models.document_processes import ProcessStatus

# ============================
# Mock Repository 구성
# ============================
class MockRepository:
    def __init__(self, mock_json):
        self.mock_json = mock_json

        # 기록용
        self.saved_segments = None
        self.updated_status = []
        self.committed = False

    async def get_speaker_texts(self, limit: int):
        class MockContent:
            speaker_segments = self.mock_json

        class MockRow:
            id = 1
            document_id = 100
            content = MockContent()

        return [MockRow()]

    async def save_keyword_result(self, document_id, segments):
        self.saved_segments = segments

    async def update_process_status(self, process_id, status):
        self.updated_status.append((process_id, status))

    async def commit(self):
        self.committed = True

# ============================
# Pytest 테스트
# ============================
@pytest.mark.asyncio
async def test_keyword_extraction_service():
    # ----------------------------
    # 🔹 Step 1: 가짜 JSON 데이터 구성
    # ----------------------------
    mock_json = {
    "pages": [
        {
            "page": 1,  # 이전: page_number -> 이제 page
            "segments": [
                {
                    "segment_id": "1_1",
                    "page": 1,  # 반드시 segment에도 page 필요
                    "speaker_name": "박주민",
                    "speaker_role": "위원장",
                    "text": "10시가 됐습니다. 좌석을 정돈해 주시기 바랍니다."
                }
            ]
        },
        {
            "page": 2,  # 이전: page_number -> page
            "segments": [
                {
                    "segment_id": "2_1",
                    "page": 2,
                    "speaker_name": "강선우",
                    "speaker_role": "위원",
                    "text": "서울 강서갑 국회의원 강선우입니다."
                },
                {
                    "segment_id": "2_2",
                    "page": 2,
                    "speaker_name": "박주민",
                    "speaker_role": "위원장",
                    "text": "다음은 김남희 위원님 인사말씀 부탁드리겠습니다."
                },
                {
                    "segment_id": "2_3",
                    "page": 2,
                    "speaker_name": "김남희",
                    "speaker_role": "위원",
                    "text": "안녕하십니까? 광명을 국회의원 김남희입니다."
                }
            ]
        }
    ]
}

    # ----------------------------
    # 🔹 Step 2: Mock Repository 주입
    # ----------------------------
    repo = MockRepository(mock_json)

    # ----------------------------
    # 🔹 Step 3: 서비스 인스턴스 생성
    # ----------------------------
    service = PdfKeywordExtractorService(repo)

    # ----------------------------
    # 🔹 Step 3-1: Kiwi Mock 처리
    # ----------------------------
    service.kiwi = MagicMock()
    mock_token = MagicMock()
    mock_token.form = "과학기술"
    service.kiwi.analyze.return_value = [[[(mock_token, "NNG", None, None)]]]

    # ----------------------------
    # 🔹 Step 4: 실행
    # ----------------------------
    await service.run_keyword_extraction(limit=1)

    # ----------------------------
    # 🔹 Step 5: 검증
    # ----------------------------
    # 결과 저장 확인
    assert repo.saved_segments is not None, "키워드 추출 결과가 저장되지 않음"

    # segments가 리스트 형태인지 확인
    assert isinstance(repo.saved_segments, list)
    assert len(repo.saved_segments) == 4, "세그먼트 개수가 잘못됨"

    # DTO 타입 확인
    assert isinstance(repo.saved_segments[0], DocumentSegmentSaveSchema)

    # 상태 업데이트 확인
    assert repo.updated_status[0][1] == ProcessStatus.KEYWORD

    # commit 호출 여부
    assert repo.committed is True

    print("\n=== 저장된 Segment DTO 샘플 ===")
    print(repo.saved_segments[0])

    print("\n테스트 성공! 모든 프로세스가 정상 작동함.")
