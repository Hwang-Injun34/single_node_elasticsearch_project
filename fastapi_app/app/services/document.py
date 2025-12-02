from typing import Optional

from app.repositories.document import DocumentRepository
from app.models.document import Document

class DocumentService: 
    def __init__(self, repo: DocumentRepository):
        self.db_repo = repo 
    
    async def get_document_context(self, doc_id: str) -> Optional[Document]:
        """
        전체 문서를 조회하여 문맥을 제공
        """
        document = await self.db_repo.get_full_context_by_id(doc_id)
        return document 
    