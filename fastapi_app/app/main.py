import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from kiwipiepy import Kiwi 
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from app.core.config import settings 
from app.core.state import state

# 내부 모듈 예시 (프로젝트별로 필요에 따라 추가)
from app.database.connection import engine, Base
from app.api.api import api_router


from app.models.document import Document
from app.models.document_segments import DocumentSegment 
from app.models.document_processes import DocumentProcess 
from app.models.document_contents import DocumentContent 


# ---------------------------
#  로깅 설정
# ---------------------------
def configure_logging():
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)  # 초기 단계는 INFO로 충분

# ---------------------------
#  애플리케이션 라이프사이클
# ---------------------------
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # 서버 시작 시 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # [Step 1] 임베딩 모델 로딩
    print("[Application Startup] 임베딩 모델 로딩 시작...")
    try:
        # 1. 임베딩 모델
        state["embedding_model"]  = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, device="cpu")

        # 2. Kiwi 형태소 분석기
        state["kiwi_instance"] = Kiwi()

        # 3. KeyBERT 모델(임베딩 모델을 사용하여 초기화)
        state["keybert_model"] = KeyBERT(model=state["embedding_model"])

        print("[Application Startup] 모든 모델 및 도구 로딩 완료")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to load embedding model: {e}")
        raise RuntimeError("Embedding model initialization failed.") from e

    yield # 서버 실행

    # [Step 2] 서버 종료 시 리소스 정리
    state.clear()
    print("[Application Shutdown] 리소스 정리 완료")

# ---------------------------
#  앱 생성 함수
# ---------------------------
def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        lifespan=app_lifespan,
        title="FastAPI Starter",
        version="0.1.0",
        docs_url="/docs",
        redoc_url=None
    )

    # CORS 미들웨어: 초기 단계는 모든 도메인 허용
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # 라우터 등록 (예시)
    app.include_router(api_router, prefix="/api/v1")

    return app




# ---------------------------
# 앱 인스턴스 생성
# ---------------------------
app = create_app()
