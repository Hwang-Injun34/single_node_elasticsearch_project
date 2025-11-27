import enum

from sqlalchemy import Column, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import relationship

from app.database.connection import Base

class ProcessStatus(str, enum.Enum):
    PENDING = "PENDING"          # 대기 중 (아직 시작 안함)
    EXTRACTED = "EXTRACTED"      # 1단계(PDF 텍스트 추출) 완료
    PARSED = "PARSED"            # 2단계(발언자 파싱) 완료 / DB 저장 완료
    COMPLETED = "COMPLETED"      # 전체 완료 (추후 인덱싱 등 포함 시)
    FAILED = "FAILED"            # 처리 실패


class DocumentProcess(Base):
    __tablename__ = "document_processes"

    id = Column(BIGINT, primary_key=True, autoincrement=True)

    # Document와 연결
    document_id = Column(BIGINT, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True)

    status = Column(
        Enum(ProcessStatus),
        default=ProcessStatus.PENDING,
        nullable=False, 
        comment="PENDING, EXTRACTED, PARSED, COMPLETED, FAILED"    
    )
    
    # 관계 설정
    document = relationship("Document", back_populates="process")

    content = relationship(
        "DocumentContent", 
        uselist=False, 
        back_populates="process", 
        cascade="all, delete-orphan"
    )

    segment = relationship(
        "DocumentSegment", 
        uselist=False, 
        back_populates="process", 
        cascade="all, delete-orphan"
    )
