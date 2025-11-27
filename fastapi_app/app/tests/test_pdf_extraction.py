import pytest
import asyncio
from unittest.mock import AsyncMock

from app.services.pdf_pipeline.p01_pdf_extraction import PdfExtractionService
from app.schema.pdf import DocumentContentSaveSchema

# Mock Repository 정의
class MockRepository:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path 
        self.saved_data = None 
        self.committed = False 
        self.status_updates = []
    
    async def get_unprocessed_pdfs(self, limit: int):
        # 실제 DB row 구조를 흉내낸 Mock 객체
        class MockDocument:
            file_path = self.pdf_path 
        
        class MockRow:
            id = 1 
            document_id = 999
            document = MockDocument()
        
        return [MockRow]
    
    async def save_extraction_result(self, process_id, save_data: DocumentContentSaveSchema):
        self.saved_data = save_data
    
    async def update_process_status(self, process_id, status):
        self.status_updates.append((process_id, status))
    
    async def commit(self):
        self.committed = True 


# 실제 테스트 코드
@pytest.mark.asyncio
async def test_pdf_extraction_service():
    # 실제 PDF 파일 경로
    pdf_path = "/Users/namgungmyeongsu/Desktop/mini-project/single_node_elasticsearch_project/fastapi_app/static/pdfs/2024-06-11_52074_제22대 제415회 1차 과학기술정보방송통신위원회.pdf"

    # Mock Repository 사용
    repo = MockRepository(pdf_path)

    # 서비스 생성
    service = PdfExtractionService(repo)

    # 실행
    await service.execute_pdf_extraction(limit=1)

    # 검증
    assert repo.saved_data is not None, "PDF 추출 결과가 저장되지 않았습니다."
    assert isinstance(repo.saved_data.compressed_page_texts, bytes), "저장된 데이터가 bytes 형태가 아닙니다."
    assert repo.committed is True, "commit()이 호출되지 않았습니다."

    print(repo.saved_data)

    print("테스트 성공! PDF 추출 및 압축, 저장까지 정상적으로 수행됨.")