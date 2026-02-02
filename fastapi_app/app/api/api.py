from fastapi import APIRouter

from .crawler import router as crawler_router 
from .admin import router as user_router 
from .pdf_pipeline import router as pdf_router
from .search import router as search_router
from .segment import router as segment_router
from .document import router as document_router

"""
제목: API 루트 라우터
목적: 도메인별 하위 라우터를 하나의 엔트리 포인트로 통합
핵심동작: 각 기능 모듈의 APIRouter를 prefix와 tags와 함께 등록
"""


api_router = APIRouter()

api_router.include_router(user_router, prefix='/admins', tags=["admins"])
api_router.include_router(crawler_router, prefix='/crawlers', tags=["crawlers"])
api_router.include_router(pdf_router, prefix='/pdf', tags=["pdf"])
api_router.include_router(search_router, prefix='/search', tags=["search"])
api_router.include_router(segment_router, prefix='/segment', tags=["segment"])
api_router.include_router(document_router, prefix='/document', tags=["document"])