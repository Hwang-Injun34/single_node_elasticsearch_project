import pytest
import asyncio
from unittest.mock import AsyncMock

from kiwipiepy import Kiwi
from app.services.pdf_pipeline.p03_track_a import PdfKeywordExtractorService
from app.schema.pdf import DocumentSegmentSaveSchema
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
async def test_keyword_extraction_with_real_data():

    # ----------------------------
    # 🔹 Step 1: 실제와 유사한 JSON 데이터 구성
    # ----------------------------
    mock_json = {
        "pages": [
            {
                "page": 1,
                "segments": [
                    {
                        "segment_id": "1_1",
                        "page": 1,
                        "speaker_name": "박주민",
                        "speaker_role": "위원장",
                        "text": (
                            "10시가 됐습니다.\n좌석을 정돈해 주시기 바랍니다.\n"
                            "성원이 되었으므로 제415회 국회(임시회) 제1차 보건복지위원회를 개회하겠습니다.\n"
                            "보고사항은 노트북 단말기에 있는 자료를 참고해 주시기 바랍니다.\n"
                            "제22대 국회 전반기 보건복지위원장으로 선출된 박주민 위원장입니다.\n"
                            "오늘은 22대 보건복지위원회를 처음으로 개회하는 날입니다만 아쉽게도 국민의힘 의원님들이 전원 불참하셨습니다.\n"
                            "의대 정원을 늘리는 문제로 의료"
                        )
                    }
                ]
            },
            {
                "page": 2,
                "segments": [
                    {
                        "segment_id": "2_1",
                        "page": 2,
                        "speaker_name": "강선우",
                        "speaker_role": "위원",
                        "text": (
                            "서울 강서갑 국회의원 강선우입니다.\n"
                            "박주민 위원장께서 말씀하셨듯이 현장의 어려움을 직접적으로 가장 많이 그리고 빠르게 느끼는 위원회가 바로 보건복지위원회입니다.\n"
                            "더불어민주당 위원님들 그리고 국민의힘 또 조국혁신당, 개혁신당 위원님들과 함께 민생 잘 챙기고 "
                            "그리고 우리 국민들의 삶에 있어서 예측 가능성이 있는 그런 대한민국 만드는 데 최선의 노력 다하겠습니다.\n"
                            "고맙습니다."
                        )
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
                        "text": (
                            "안녕하십니까? 광명을 국회의원 김남희입니다.\n"
                            "선배·동료 위원님께 인사드립니다.\n"
                            "저는 복지 분야에서 오랫동안 활동을 해 왔고요. 저의 전공을 살려서 한국 사회의 가장 큰 위기인 "
                            "저출생·고령화 사회를 대응하는 정책을 만드는 데 앞장서겠습니다."
                        )
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
    # 🔹 Step 3: 서비스 인스턴스 생성 (실제 Kiwi 사용)
    # ----------------------------
    service = PdfKeywordExtractorService(repo)

    # ----------------------------
    # 🔹 Step 4: 실행
    # ----------------------------
    await service.run_keyword_extraction(limit=1)

    # ----------------------------
    # 🔹 Step 5: 검증
    # ----------------------------
    # 결과 저장 확인
    assert repo.saved_segments is not None, "키워드 추출 결과가 저장되지 않음"
    assert isinstance(repo.saved_segments, list)
    assert len(repo.saved_segments) == 4, "세그먼트 개수가 잘못됨"
    assert isinstance(repo.saved_segments[0], DocumentSegmentSaveSchema)

    # 상태 업데이트 확인
    assert repo.updated_status[0][1] == ProcessStatus.KEYWORD

    # commit 호출 여부
    assert repo.committed is True

    print("\n=== 저장된 Segment DTO 샘플 ===")
    print(repo.saved_segments[0])

    print("\n테스트 성공! 모든 프로세스가 정상 작동함.")
