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
    total_hits: int          # 서비스에서 "total_hits"로 줘야 함
    execution_time: float    # 서비스에서 "execution_time"으로 줘야 함
    es_took: int             # 서비스에서 "es_took"으로 줘야 함
    results: List[SearchResultItem]