from sqlalchemy import Column, Boolean, ForeignKey, Text, JSON, LargeBinary
from sqlalchemy.dialects.mysql import BIGINT, LONGTEXT
from sqlalchemy.orm import relationship

from app.database.connection import Base


class DocumentContent(Base):
    __tablename__ = "document_contents"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    
    process_id = Column(BIGINT, ForeignKey("document_processes.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # 페이지별 텍스트 저장
    compressed_page_texts = Column(LargeBinary, nullable=True)

    # 화자별 텍스트 저장
    speaker_segments = Column(JSON, nullable=True)

    # 관계 설정
    process = relationship(
        "DocumentProcess", 
        back_populates="content"
    )