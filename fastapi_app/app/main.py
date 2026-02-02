import torch
import logging
import sys
from sklearn.feature_extraction.text import CountVectorizer

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

# ===============================
# 제목: 커스텀 불용어 및 토크나이저 설정
# 목적: 키워드 추출 시 의미 없는 단어 제거 및 형태소 기반 토큰화 수행
# 핵심동작: Kiwi 형태소 분석기로 명사 중심 토큰만 필터링
# ===============================
CUSTOM_STOPWORDS = {
    "의원", "대표발의", "발의", "소위원장", "위원장", "전문위원",
    "차관", "장관", "정부", "부처", "지방자치단체",
    "일부", "개정", "법률안", "의결", "검토", "보고",
    "수립", "운영", "지원", "대상"
}


def kiwi_tokenizer(text: str):
    tokens = state["kiwi_instance"].analyze(text)
    result = []

    if tokens:
        for t in tokens[0][0]:
            if (
                t.tag in {"NNG", "NNP", "SL"}
                and len(t.form) > 1
                and t.form not in CUSTOM_STOPWORDS
            ):
                result.append(t.form)
    return result


# ===============================
# 제목: 로깅 설정
# 목적: 애플리케이션 전역 로그 출력 포맷 및 레벨 초기화
# 핵심동작: stdout 핸들러 등록 및 로그 레벨을 INFO로 설정
# ===============================
def configure_logging():
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)  # 초기 단계는 INFO로 충분

# ===============================
# 제목: 애플리케이션 라이프사이클 관리
# 목적: 서버 시작/종료 시 리소스 초기화 및 정리 수행
# 핵심동작: DB 테이블 생성, ML 모델 로딩, 종료 시 state 정리
# ===============================
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # 서버 시작 시 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # [Step 1] 임베딩 모델 로딩
    print("[Application Startup] 임베딩 모델 로딩 시작...")
    try:
        # 1. 임베딩 모델
        state["embedding_model"] = SentenceTransformer(
            settings.SBERT_MODEL_PATH, 
            device="cuda" if torch.cuda.is_available() else "cpu"
        )

        # 2. Kiwi 형태소 분석기
        state["kiwi_instance"] = Kiwi()

        # 3. KeyBERT 모델(임베딩 모델을 사용하여 초기화)
        state["keybert_model"] = KeyBERT(model=state["embedding_model"])

        state["keybert_vectorizer"] = CountVectorizer(
            tokenizer=kiwi_tokenizer, 
            token_pattern=None,
            ngram_range=(1, 2)
        )

        print("[Application Startup] 모든 모델 및 도구 로딩 완료")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to load embedding model: {e}")
        raise RuntimeError("Embedding model initialization failed.") from e

    yield # 서버 실행

    # [Step 2] 서버 종료 시 리소스 정리
    state.clear()
    print("[Application Shutdown] 리소스 정리 완료")

# ===============================
# 제목: FastAPI 앱 팩토리
# 목적: FastAPI 애플리케이션 인스턴스를 설정 및 생성
# 핵심동작: 라이프사이클 등록, CORS 설정, 라우터 마운트
# ===============================
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




# ===============================
# 제목: 애플리케이션 엔트리포인트
# 목적: ASGI 서버에서 참조할 FastAPI 앱 객체 생성
# 핵심동작: create_app() 호출 결과를 app 변수에 할당
# ===============================
app = create_app()