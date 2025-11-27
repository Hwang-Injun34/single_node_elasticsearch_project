# test_pdf_embedding_service.py
import pytest
import asyncio
import numpy as np  # 🔥 numpy 임포트 필수!
from unittest.mock import AsyncMock, MagicMock

from app.services.pdf_pipeline.p03_track_b import PdfEmbeddingExtractorService
from app.repositories.pdf_process.p03_track_b import PdfEmbeddingExtractorRepository

# ============================
# Mock Repository 구성
# ============================
class MockPdfRepo:
    def __init__(self):
        # 세그먼트 더미 생성
        self.segments = [
            MagicMock(id=1, original_text="안녕하세요"),
            MagicMock(id=2, original_text="반갑습니다"),
        ]
        self.updated_vectors = []

    async def get_segments_without_vector(self, limit: int):
        return self.segments[:limit]

    async def update_vectors_bulk(self, processed_data):
        self.updated_vectors.extend(processed_data)

# ============================
# Pytest 테스트
# ============================
@pytest.mark.asyncio
async def test_embedding_extraction_service():
    # 1️⃣ Mock Repo 생성
    mock_repo = MockPdfRepo()

    # 2️⃣ 서비스 인스턴스 생성
    service = PdfEmbeddingExtractorService(db_p03_track_b=mock_repo)

    # 🔥 [수정 포인트] 모델 encode()의 반환값을 numpy array로 설정
    mock_vector = [0.1] * 768
    
    # ⚠️ 중요: 서비스 코드 내부에서 .tolist()를 호출하므로, 
    # Mock이 반환하는 값은 반드시 numpy array여야 함.
    mock_numpy_result = np.array([mock_vector, mock_vector]) 
    
    service.model.encode = MagicMock(return_value=mock_numpy_result)

    # 3️⃣ 실행
    await service.run_embedding_extraction(limit=2)

    # 4️⃣ 검증
    assert len(mock_repo.updated_vectors) == 2
    for item in mock_repo.updated_vectors:
        assert "id" in item
        assert "embedding_vector" in item
        assert len(item["embedding_vector"]) == 768

    print("\n✅ 테스트 성공! 임베딩이 정상적으로 처리되고 DB에 저장됨.")