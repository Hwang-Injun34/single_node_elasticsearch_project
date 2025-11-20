from sqlalchemy import Column, String, Date, Text, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import BIGINT 
from app.database.connection import Base 

class ReportEra(Base):
    __tablename__= "report_eras"

    # ID 
    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

    # 보고서 ID 
    report_id = Column(BIGINT(unsigned=True), ForeignKey("reports.report_id"), nullable=False, index=True)

    # 유적 성격 : '생활유적', '성곽'
    site_type = Column(String(50), nullable=True)

    # 시대 : '통일신라', '조선시대'
    era = Column(String(50), nullalbe=True)
