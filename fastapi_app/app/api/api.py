from fastapi import APIRouter

from .crawler import router as crawler_router 
from .user import router as user_router 

api_router = APIRouter()

api_router.include_router(user_router, prefix='/users', tags=["users"])
api_router.include_router(crawler_router, prefix='/crawlers', tags=["crawlers"])
