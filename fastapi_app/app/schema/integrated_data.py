from pydantic import BaseModel, Field
from datetime import date 
from typing import List, Optional


# -----------------------------
# /segment/{segment_id} 전용
# -----------------------------
class DocumentMeta(BaseModel):
    doc_id: int = Field(..., alias="id")
    title: str
    className: str
    committeeName: str 
    confDate: date | None = None 
    pdfLinkUrl: str | None = None 

    class Config:
        # ORM 모드 활성화(SQLAlchemy 객체에서 필드 이름을 매핑할 때 필요)
        from_attributes: True


class SegmentDetail(BaseModel):
    segment_id: int = Field(..., alias="id")
    content: str = Field(..., alias="original_text")
    page_number: int 
    speaker_name: str 
    speaker_role: str 
    keywords: Optional[List[str]] = None 

    document: DocumentMeta 

    class Confing: 
        from_attributes = True 
        # segment_id에 alias가 적용되도록 허용
        populate_by_name = True

# -----------------------------
# /document/{doc_id} 전용
# -----------------------------
class SegmentBase(BaseModel):
    segment_id: int = Field(..., alias="id")
    original_text: str
    page_number: int
    speaker_name: str
    speaker_role: str

    class Config:
        from_attributes = True


class DocumentDetail(BaseModel):
    doc_id: int = Field(..., alias="id")
    title: str
    className: str 
    committeeName: str
    confDate: date | None = None
    pdfLinkUrl: str 
    file_path: str 
    
    segments: List[SegmentBase] 

    class Config:
        from_attributes = True