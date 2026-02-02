from fastapi import APIRouter, Depends, Path, status, HTTPException
from fastapi.responses import FileResponse

from app.services.document import DocumentService 
from app.dependencies.document import get_document_service
from app.schema.integrated_data import DocumentDetail

router = APIRouter()

@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document_context( 
    doc_id: str = Path(..., description="조회할 문서의 고유 ID"), 
    document_service: DocumentService = Depends(get_document_service)
): 
    """
    제목: 문서 상세 조회 API
    목적: 특성 문서 ID에 해당하는 메타데이터 및 본문 정보 제공
    핵심동작: 문서 서비스 조회 -> 없으면 404 -> 데이터 반환
    """
    document_data = await document_service.get_document_context(doc_id)

    if not document_data: 
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document_data


@router.get("/{doc_id}/pdf", response_model=None, status_code=status.HTTP_200_OK)
async def server_document_pdf(
    doc_id: str = Path(..., description="다운로드/미리보기할 문서 ID"),
    document_service: DocumentService = Depends(get_document_service)
): 
    """
    제목: 문서 PDF 스트리밍 API 
    목적: 특정 문서의 PDF 파일을 브라우저에서 미리보기/다운로드 제공
    핵심동작: 파일 경로 조회 -> FileResponse로 스트리밍 반환
    """
    file_path_obj = await document_service.get_pdf_file_path(doc_id)

    if not file_path_obj: 
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    return FileResponse(
        path=str(file_path_obj), 
        media_type="application/pdf", 
        filename=f"{doc_id}.pdf",
        # inline: 다운로드 대신 브라우저 내에서 미리보기를 시도하도록 유도
        headers={"Content-Disposition": f"inline; filename={doc_id}.pdf"} 
    )