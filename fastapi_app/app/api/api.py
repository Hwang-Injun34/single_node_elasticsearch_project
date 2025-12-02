from fastapi import APIRouter

from .crawler import router as crawler_router 
from .user import router as user_router 
from .pdf_pipeline import router as pdf_router
from .search import router as search_router
from .segment import router as segment_router
from .document import router as document_router

api_router = APIRouter()

api_router.include_router(user_router, prefix='/users', tags=["users"])
api_router.include_router(crawler_router, prefix='/crawlers', tags=["crawlers"])
api_router.include_router(pdf_router, prefix='/pdf', tags=["pdf"])
api_router.include_router(search_router, prefix='/search', tags=["search"])
api_router.include_router(segment_router, prefix='/segment', tags=["segment"])
api_router.include_router(document_router, prefix='/document', tags=["document"])