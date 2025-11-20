from sqlalchemy import Column, String, Date, Text, DateTime 
from sqlalchemy.dialects.mysql import BIGINT 
from app.database.connection import Base 

class Report(Base):
    __tablename__ = "reports"
    
    # 보고서 ID(PK)
    report_id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    
    # -- Main Info --
    # 허가번호
    permit_number = Column()
    # 보고서명
    title = Column()
    # 유적/사업명
    project_name = Column(String(255), index=True, nullable=True)
    # 발간기관
    agency = Column(String(100), index=True, nullable=True)
    # 제출일
    publish_date = Column(Date, nullable=True)

    # -- Region info --
    # 조사 시도
    region_sido = Column(String(50), index=True, nullable=True)
    # 조사 시군구
    region_sigungu = Column(String(50), index=True, nullable=True)
    

    # 주소
    address = Column(String(500), nullable=True)
    # 조사면적 
    area = Column(String(50), nullable=True)

    # 조사 시작일
    investigation_start = Column(Date, nullable=True)
    # 조사 종료일
    investigation_end = Column(Date, nullable=True)

    # -- Contents --
    # 시대/성격
    era_raw_text = Column(Text, nullable=True)
    # PDF 경로
    file_url = Column(String(500), nullable=True)
    # 본문 텍스트
    full_text = Column(Text, nullable=True)