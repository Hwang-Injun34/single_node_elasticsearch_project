from pydantic import BaseModel, Field
from typing import List, Optional 

class SearchResultItem(BaseModel):
    score: float
    segment_id: str
    content_text: str 
    highlight: str 
    speaker: str 
    committee_name: str
    conf_date: str
    keywords: Optional[List[str]] = None

    doc_id: str 
    title: str


class SearchResponse(BaseModel):
    total: int 
    took: float 
    results: List[SearchResultItem]