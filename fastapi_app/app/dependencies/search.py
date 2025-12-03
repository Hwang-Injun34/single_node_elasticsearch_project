from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer

from app.services.search import SearchService
from app.dependencies.model import get_embedding_model 

async def get_search_service(
    model: SentenceTransformer = Depends(get_embedding_model)
)-> SearchService:
    return SearchService(model_instance=model)