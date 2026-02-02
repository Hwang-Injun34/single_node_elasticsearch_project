from typing import Optional
from pathlib import Path

from app.core.config import settings
from app.repositories.document import DocumentRepository
from app.models.document import Document


# ======================================================
# [제목] Elasticsearch 클라이언트 연결 관리
# ------------------------------------------------------
# [목적]
#  - FastAPI 애플리케이션과 Elasticsearch 간의 연결을 중앙에서 관리한다.
#  - 비동기/동기 클라이언트를 분리하여 런타임 API 요청과
#    초기화 스크립트·배치 작업에서 각각 적절히 사용하도록 한다.
#
# [핵심 동작]
#  - AsyncElasticsearch: API 요청 처리용 비동기 클라이언트 생성
#  - Elasticsearch: 인덱스 초기화, 마이그레이션 등 동기 작업용 클라이언트 생성
#  - check_es_connection(): 서버 시작 시 연결 상태를 ping으로 검증
# ======================================================

class DocumentService: 
    def __init__(self, repo: DocumentRepository):
        self.db_repo = repo 
        self.security_base = settings.CONTAINER_ROOT_PATH
    
    async def get_document_context(self, doc_id: str) -> Optional[Document]:
        """
        전체 문서를 조회하여 문맥을 제공
        """
        try:
            int_id = int(doc_id)
        except ValueError: 
            print(f"DEBUG: Invalid doc_id format: {doc_id}")
            return None
        
        print(f"DEBUG: Querying DB for doc_id (INT): {int_id}")
        document = await self.db_repo.get_full_context_by_id(int_id)
        
        if not document: 
            print(f"DEBUG: Document ID {int_id} not found in DB.")
        return document 
    

    async def get_pdf_file_path(self, doc_id: str) -> Optional[Path]:
        """
        DB에 저장된 컨테이너 내부 경로를 조회하고, 보안 검사를 거쳐 Path 객체를 반환
        """
        int_id = int(doc_id)
        document = await self.db_repo.get_metadata_only_by_id(int_id)

        if not document or not document.file_path: 
            return None 
        
        static_file_path = document.file_path 
        full_path = Path(static_file_path)

        # 1. 보안 검사: 경로 이탈(Path Traversal) 방지
        try: 
            full_path.relative_to(self.security_base)
        except ValueError: 
            # 예상된 /app/static/pdfs 경로 바깥으로 접근 시도(보안 위반)
            print(f"SECURITY ALERT: Path Traversal attempt detected: {full_path}")
            return None

        # 2. 파일 존재 여부 확인(컨테이너 내부 파일 시스템 기준)
        # exists()와 is_file()은 동기 호출이지만, 파일 I/O는 FileResponse가 처리하므로 안전
        if full_path.exists() and full_path.is_file():
            return full_path 

        print(f"FILE NOT FOUND in container: {full_path}")
        return None 
    
