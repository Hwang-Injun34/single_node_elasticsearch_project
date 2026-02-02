import pdfplumber
import asyncio
import zlib
import unicodedata

from app.repositories.pdf_process.p01_pdf_extraction import PdfExtractionRepository
from app.schema.pdf import DocumentContentSaveSchema, TotalPageTextSchema, PageTextSchema
from app.models.document_processes import ProcessStatus

# ===============================
# 제목: PDF 텍스트 추출 서비스
# 목적: PDF 파일을 페이지 단위 텍스트로 변환하여 DB에 저장
# 핵심동작: PDF → 텍스트 추출 → 압축 → 상태 업데이트
# ===============================
class PdfExtractionService:
    def __init__(self, db_p01: PdfExtractionRepository):
        self.db_repo = db_p01
    
    # -------------------------
    # 제목: PDF 추출 메인 실행 함수
    # 목적: 미처리 PDF 문서를 조회하여 전체 추출 파이프라인 수행
    # 핵심동작: 대상 조회 → 텍스트 추출 → 저장 → 상태 변경
    # -------------------------
    async def execute_pdf_extraction(self, limit: int = 3):
        """
        PDF 텍스트 추출 전체 프로세스를 실행하는 메인 함수
        """

        # [Step 1] Repository를 통해 대상 조회
        targets = await self.db_repo.get_unprocessed_pdfs_by_status(limit)

        if not targets:
            print("처리할 PDF가 없음")
            return 
        
        processed_count = 0

        for document_check_row in targets:
            try:
                if not document_check_row.document or not document_check_row.document.file_path:
                    print(f"[Skip] ID {document_check_row}: 파일 경로 없음")
                    continue 

                file_path = document_check_row.document.file_path 
                process_id = document_check_row.id 
                document_id = document_check_row.document_id

                print(f"[Start] Document ID {document_id}: {file_path}")


                # [Step 2] 텍스트 추출(ThreadPool에서 실행) - TotalPageTextSchema
                total_page_data: TotalPageTextSchema = await self._extract_text_from_pdf(file_path)

                # [Step 3] 데이터 압축 (TotalPageTextSchema 활용)
                json_str = total_page_data.model_dump_json(exclude_none=True)

                # 압축 (str -> bytes -> compressed bytes)
                compressed_data = zlib.compress(json_str.encode('utf-8'))

                # [Step 4] 저장용 스키마 생성 (DocumentContentSaveSchema 적용)
                save_data = DocumentContentSaveSchema(
                    compressed_page_texts= compressed_data
                )


                await self.db_repo.save_extraction_result(process_id, save_data)
                await self.db_repo.update_process_status(process_id, ProcessStatus.EXTRACTED)
                processed_count += 1 
                print(f"[성공] Document ID {document_id} 추출 성공")

            except Exception as e:
                print(f"[Error] Document ID {document_id} 처리 중 오류: {e}")
                await self.db_repo.update_process_status(process_id, ProcessStatus.FAILED)

        # [Step 5] 커밋
        if processed_count > 0: 
            await self.db_repo.commit()
            print(f"총 {processed_count}건 처리 완료 및 커밋됨.")

    # -------------------------
    # 제목: PDF 텍스트 비동기 추출 래퍼
    # 목적: 동기 PDF 라이브러리를 비동기 환경에서 안전하게 실행
    # 핵심동작: asyncio.to_thread()로 동기 함수 실행
    # -------------------------
    async def _extract_text_from_pdf(self, path: str) -> list:
        """
        PyMuPDF는 동기 라이브러리 -> asyncio.to_thread() 사용해 비동기 처리
        """
        return await asyncio.to_thread(self._sync_extract_pdf, path)


    # -------------------------
    # 제목: PDF 텍스트 동기 추출 함수
    # 목적: pdfplumber로 페이지별 텍스트를 실제 추출
    # 핵심동작: 페이지 순회 → 텍스트 정규화 → 스키마 변환
    # -------------------------
    def _sync_extract_pdf(self, path: str) -> TotalPageTextSchema:
        pages_list = []
        
        try:
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages):
                    # extract_text 옵션 설명:
                    # x_tolerance: 글자 사이 간격이 이 값보다 크면 띄어쓰기로 인식 (기본: 3)
                    # y_tolerance: 줄 간격 인식 (기본: 3)
                    # keep_blank_chars: False (불필요한 공백 제거)
                    text = page.extract_text(x_tolerance=2, y_tolerance=3, keep_blank_chars=False)
                    print(text)
                    if not text:
                        text = ""
                    
                    # 유니코드 정규화
                    text = unicodedata.normalize("NFC", text)
                    
                    pages_list.append(PageTextSchema(page_num=i+1, text=text))
                    
        except Exception as e:
            print(f"PDF 열기 실패 ({path}): {e}")
            raise e

        return TotalPageTextSchema(page_list=pages_list)
