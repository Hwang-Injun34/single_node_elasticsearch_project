from sqlalchemy import Column, Boolean, ForeignKey, Text, JSON, String
from sqlalchemy.dialects.mysql import BIGINT, LONGTEXT
from sqlalchemy.orm import relationship

from app.database.connection import Base


class DocumentSegment(Base):
    __tablename__ = "document_segments"

    id = Column(BIGINT, primary_key=True, autoincrement=True)

    # 원본 문서와의 연결(1:N)
    document_id = Column(BIGINT, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    # 세그먼트 식별 정보
    page_number = Column(BIGINT, nullable=False)

    # 발언자 정보
    speaker_name = Column(String(50), nullable=True, index=True)
    speaker_role = Column(String(50), nullable=True)

    original_text = Column(LONGTEXT, nullable=False) 

    # Track A 결과
    keyworkds = Column(JSON, nullable=True)


    # Track B 결과
    embedding_vector = Column(JSON, nullable=True)


    # 관계 설정 
    ducment = relationship("Document", back_populates="segments")