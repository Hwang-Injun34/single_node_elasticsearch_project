from pydantic import BaseModel, Field, AnyUrl
from datetime import date, datetime
from typing import Optional

# -------------------------------
# 입력용 스키마 (Create)
# -------------------------------
class DocumentCreate(BaseModel):
    className: str | None = Field(None, description="회의종류")
    committeeName: str | None = Field(None, description="위원회")
    confDate: date | None = Field(None, description="회의일")
    conferNum: str = Field(..., description="원본 사이트 문서 ID (중복 체크용)")
    pdfLinkUrl: str = Field(..., description="PDF 다운로드 URL")
    file_path: str | None = Field(None, description="서버 PDF 위치")
    title: str = Field(..., description="회의명")

    model_config = {
        "from_attributes": True,  # SQLAlchemy 모델에서 바로 생성 가능
        "extra": "forbid",        # 불필요한 필드 금지
    }


# -------------------------------
# 크롤링 요청 필터 스키마
# -------------------------------
class CrawlerFilter(BaseModel):
    limit: int = Field(10, description="수집할 최대 문서 개수 (-1: 전체 수집)")
    title: Optional[str] = Field(None, description="제목 검색 - 예: 22대")
    beginDate: Optional[date] = Field(None, description="검색 시작일 (YYYY-MM-DD)")
    endDate: Optional[date] = Field(None, description="검색 종료일 (YYYY-MM-DD)")


# -------------------------------
# 출력용 스키마 (Read)
# -------------------------------
class DocumentRead(DocumentCreate):
    id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

