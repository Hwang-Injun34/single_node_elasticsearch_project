# app/F11_search/doc_converter.py

from typing import Any, Dict, Optional, List

# Feed 모델 및 관련 모델 import (경로는 실제 프로젝트 구조에 맞게 확인)
from app.F7_models.feeds import Feed

# --- Helper Function ---

def _calculate_average_rating(ratings: List[Any]) -> float:
    """ratings 리스트에서 평균 점수를 계산합니다."""
    if not ratings:
        return 0.0
    # 'score' 속성이 없는 경우를 대비하여 getattr 사용
    total_score = sum(getattr(r, 'score', 0) for r in ratings)
    return round(total_score / len(ratings), 2)

# --- Main Converter Function ---

def convert_feed_to_document(feed: Feed) -> Dict[str, Any]:
    """
    Feed SQLAlchemy 모델 객체를 Elasticsearch 인덱스 문서(딕셔너리)로 변환합니다.

    [중요] 이 함수를 호출하기 전에 SQLAlchemy 쿼리에서 Eager Loading(예: joinedload, selectinload)을 사용하여
    'organization', 'category', 'ratings', 'bookmarks' 관계를 미리 로드해야 N+1 쿼리 문제를 방지할 수 있습니다.
    
    Args:
        feed: 변환할 Feed 모델 인스턴스

    Returns:
        Elasticsearch 문서 형식의 딕셔너리
    """
    # 1. 관계(relationship) 데이터 안전하게 추출
    org_data = feed.organization if hasattr(feed, 'organization') and feed.organization else None
    cat_data = feed.category if hasattr(feed, 'category') and feed.category else None
    ratings_data = getattr(feed, 'ratings', [])
    bookmarks_data = getattr(feed, 'bookmarks', [])

    # 2. 검색 대상이 될 'content' 필드를 위해 주요 텍스트 필드 통합
    #    filter(None, ...)은 None이나 빈 문자열을 제외하고 합쳐줍니다.
    content_parts = [
        getattr(feed, 'title', ''),
        getattr(feed, 'summary', ''),
        getattr(feed, 'original_text', '')
    ]
    full_content = ' '.join(filter(None, content_parts))
    
    # 3. INDEX_MAPPING에 정의된 구조에 맞춰 딕셔너리(문서) 생성
    document = {
        # --- Core Identifiers ---
        "id": str(feed.id),
        "type": "정책",  # Feed 모델은 '정책' 유형으로 고정 (API 명세의 'types' 필터와 연관)

        # --- Searchable Text Fields ---
        "title": getattr(feed, 'title', None),
        "summary": getattr(feed, 'summary', None),
        "original_text": getattr(feed, 'original_text', None),
        "content": full_content,

        # --- Foreign Keys (RDBMS 참조용) ---
        "organization_id": getattr(feed, 'organization_id', None),
        "category_id": getattr(feed, 'category_id', None),

        # --- Filtering & Aggregation Fields ---
        "organization": {
            "id": org_data.id,
            "name": org_data.name,
            "logo_url": getattr(org_data, 'icon_path', None)
        } if org_data else None,
        "category": {
            "id": cat_data.id,
            "name": cat_data.name
        } if cat_data else None,
        "tags": [],  # Feed 모델에 태그 기능이 추가되면 여기에 구현

        # --- Sorting & Date Filtering Fields ---
        "published_date": feed.published_date.isoformat() if getattr(feed, 'published_date', None) else None,
        "view_count": getattr(feed, 'view_count', 0),
        "average_rating": _calculate_average_rating(ratings_data),
        "bookmark_count": len(bookmarks_data),

        # --- Retrieval-only Fields ---
        "url": f"/feed/{feed.id}",  # API 응답에 포함될 상세 페이지 URL
        "image_path": None,  # Feed 모델에는 해당 필드가 없으므로 None

        # --- 확장 필드 ---
        "metadata": {},  # 추후 추가될 수 있는 기타 정보를 위한 공간
    }
    
    return document