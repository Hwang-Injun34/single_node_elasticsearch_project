from fastapi import APIRouter, Depends, Path, HTTPException

from app.services.document import DocumentService 
from app.dependencies.document import get_document_service
from app.schema.integrated_data import DocumentDetail

router = APIRouter()

@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document_context( 
    doc_id: str = Path(..., description="조회할 문서의 고유 ID"), 
    document_service: DocumentService = Depends(get_document_service)
): 
    document_data = await document_service.get_document_context(doc_id)

    if not document_data: 
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document_data