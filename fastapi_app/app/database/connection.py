from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base 
from typing import AsyncGenerator 
from app.core.config import settings 

"""
제목: 비동기 DB 엔진 및 세션 설정
목적: FastAPI 환경에서 안전한 비동기 DB 접근 구성
핵심동작: 엔진 생성 -> 세션 팩토리 구성 -> ORM Base 정의
"""

# [간단 설명]
# engine = DB 연결 엔진
# AsyncSessionLocal = 세션을 만들어주는 공장
# session = 실제 쿼리를 실행하는 객체
# Base = ORM 모델들이 상속하는 부모 클래스
# get_db = FastAPI에서 안전한 DB 세션을 제공하는 의존성 함수

# 엔진 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,    # 개발 중엔 쿼리 로그 출력
    pool_size=10,           # 커넥션 풀 크기
    max_overflow=20,        # 오버플로우 허용량
    pool_pre_ping=True,     # 연결 끊김 자동 감지
    # Docker 네트워크 내에서는 DNS 해석 문제 등이 있을 수 있어 타임아웃 설정 권장
    pool_recycle=3600,      # 1시간마다 연결 재생성
)


# 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 모델 Base 
Base = declarative_base()
