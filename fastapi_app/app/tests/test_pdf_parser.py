import pytest
import asyncio
import zlib
import json
from unittest.mock import AsyncMock, MagicMock

from app.services.pdf_pipeline.p02_pdf_transcript_parser import PdfTranscriptParserService
from app.schema.pdf import DocumentPageSegmentsSchema, SegmentSchema
from app.models.document_processes import ProcessStatus

# -------------------------------
# 테스트용 압축 데이터 생성
# -------------------------------
def create_compressed_pages(pages):
    # TotalPageTextSchema 형태 맞춤
    total_pages_data = {"page_list": pages}
    json_bytes = json.dumps(total_pages_data).encode('utf-8')
    return zlib.compress(json_bytes)

@pytest.mark.asyncio
async def test_segmentize_pages():
    # Mock DB Repository
    mock_repo = MagicMock()
    mock_repo.get_unprocessed_pdfs = AsyncMock()
    mock_repo.save_transcript_parser_result = AsyncMock()
    mock_repo.update_process_status = AsyncMock()
    mock_repo.commit = AsyncMock()

    # 테스트용 PDF 데이터
    pages = [
        {
            "page_num": 1,
            "text": "◯홍길동 위원\n안녕하세요.\n오늘 회의 시작하겠습니다."
        },
        {
            "page_num": 2,
            "text": "◯김철수 위원\n안녕하세요.\n회의 진행 부탁드립니다.\n10시30분 산회"
        }
    ]

    compressed_data = create_compressed_pages(pages)

    # 반환값 설정
    process_row = MagicMock()
    process_row.id = 1
    process_row.document_id = 101
    process_row.content.compressed_page_texts = compressed_data

    mock_repo.get_unprocessed_pdfs.return_value = [process_row]

    # 서비스 인스턴스 생성
    service = PdfTranscriptParserService(mock_repo)

    # segmentize_pages 실행
    processed_count = await service.segmentize_pages(limit=1)

    # assert 처리 건수
    assert processed_count == 1

    # 저장 호출 검증
    assert mock_repo.save_transcript_parser_result.called
    saved_pages: DocumentPageSegmentsSchema = mock_repo.save_transcript_parser_result.call_args[0][1]
    
    # 페이지별 segment 개수 확인
    assert len(saved_pages.pages) == 2
    assert len(saved_pages.pages[0].segments) == 1
    assert len(saved_pages.pages[1].segments) == 1

    # 첫 페이지 segment 내용 검증
    first_segment: SegmentSchema = saved_pages.pages[0].segments[0]
    assert first_segment.speaker_name == "홍길동"
    assert first_segment.speaker_role == "위원"
    assert "안녕하세요." in first_segment.text

    # 두 번째 페이지 segment 내용 검증
    second_segment: SegmentSchema = saved_pages.pages[1].segments[0]
    assert second_segment.speaker_name == "김철수"
    assert second_segment.speaker_role == "위원"
    assert "산회" not in second_segment.text  # 산회 이전 텍스트까지만 포함
