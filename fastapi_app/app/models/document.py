from sqlalchemy import Column, String, DateTime, Date
from sqlalchemy.dialects.mysql import BIGINT
from datetime import datetime
from app.database.connection import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="내부 관리용 고유 ID")
    
    parliament = Column(String(50), nullable=True, comment="제00대국회")
    meeting_series = Column(String(50), nullable=True, comment="제 00회")
    meeting_number = Column(String(50), nullable=True, comment="00차")
    title = Column(String(255), nullable=False, comment="문서 제목")
    
    file_id = Column(String(50), nullable=False, comment="원본 사이트 문서 ID (중복 체크용)")
    file_url = Column(String(500), nullable=False, comment="PDF 다운로드 URL")
    file_path = Column(String(500), nullable=True, comment="서버 PDF 위치")
    
    meeting_date = Column(Date, nullable=True, index=True, comment="회의일")
    created_at = Column(DateTime, default=datetime.utcnow, comment="데이터 등록 일시")