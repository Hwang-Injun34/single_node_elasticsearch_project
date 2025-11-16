# app/F11_search/ES7_query_builder.py

import logging
from typing import Dict, Any, List, Optional
from app.F6_schemas.search import SearchQuery

logger = logging.getLogger(__name__)

# --- 내부 헬퍼 함수 ---

def _build_filter_clause(query_params: SearchQuery) -> List[Dict[str, Any]]:
    """
    쿼리 파라미터에서 필터링 관련 조건(기관, 카테고리, 유형, 날짜 범위 등)을 추출하여
    Elasticsearch의 filter 절로 구성
    filter는 must와 다르게 relevance 점수 계산에 영향을 주지 않음
    """
    filters = []
    
    # 기관명에 대한 필터: 쉼표로 구성된 문자열을 리스트로 반환
    if query_params.organizations:
        # 쉼표로 분리하고, 각 항목의 앞뒤 공백 제거, 빈 항목은 제외
        org_list = [org.strip() for org in query_params.organizations.split(',') if org.strip()]
        if org_list:
            filters.append({"terms": {"organization.name": org_list}})

    # 카테고리에 대한 필터
    if query_params.categories:
        cat_list = [cat.strip() for cat in query_params.categories.split(',') if cat.strip()]
        if cat_list:
            filters.append({"terms": {"category.name": cat_list}})

    # 콘텐츠 유형(type)에 대한 필터
    if query_params.types:
        type_list = [t.strip() for t in query_params.types.split(',') if t.strip()]
        if type_list:
            filters.append({"terms": {"type": type_list}})

    # 날짜 범위 필터(published_date 기준)
    date_range = {}
    if query_params.date_from:
        date_range["gte"] = query_params.date_from.isoformat()
    if query_params.date_to:
        date_range["lte"] = query_params.date_to.isoformat()
    if date_range:
        filters.append({"range": {"published_date": date_range}})
        
    return filters


def _build_must_clause(keyword: Optional[str]) -> List[Dict[str, Any]]:
    """
    검색 키워드를 기반으로 must 절을 구성
    검색 키워드가 없을 경우 must_all로 전체 문서를 반환
    """
    if not keyword:
        return [{"match_all": {}}] # 키워드가 없으면 전체 결과 반환
    
    # multi_match: 여러 필드에 대해 한 번에 검색
    return [{
        "multi_match": {
            "query": keyword,
            "fields": [
                "title^2",              # title 필드에는 가중치 2배
                "summary^1.5",          # summary 필드는 1.5배
                "original_text^1.0"     # 원문에는 기본 가중치
            ],
            "type": "best_fields",      # 가장 잘 맞는 필드를 우선
            "fuzziness": "AUTO"         # 자동 오타 허용 (편의성)
        }
    }]

def _build_sort_clause(sort_option: str) -> List[Dict[str, Any]]:
    """
    사용자가 선택한 정렬 옵션에 따라 sort 절을 구성
    기본값 relevance(연관도 높은 순)
    """
    sort_options = {
        "latest": [{"published_date": "desc"}], # 최신순
        "oldest": [{"published_date": "asc"}],  # 오래된순
        "views": [{"view_count": "desc"}],      # 조회수순
        "rating": [{"average_rating": "desc"}], # 평점순
        "relevance": [{"_score": "desc"}]       # 연관도순(기본)
    }
    return sort_options.get(sort_option, sort_options["relevance"])

def _build_aggregations() -> Dict[str, Any]:
    """
    검색 결과 집계를 위한 aggregation 절 구성
    각 필터 항목의 분포 정보를 얻기 위해 사용
    """

    return {
        "organizations": {"terms": {"field": "organization.name", "size": 20}}, # 상위 20개 기관
        "categories": {"terms": {"field": "category.name", "size": 20}}, # 상위 20개 카테고리
        "types": {"terms": {"field": "type", "size": 10}}, # 콘텐츠 유형별 분포
        "date_ranges": {
            "date_range": {
                "field": "published_date", # 날짜 기준
                "ranges": [
                    {"from": "now-7d/d", "to": "now/d", "key": "최근 1주일"},
                    {"from": "now-1M/d", "to": "now/d", "key": "최근 1개월"},
                    {"from": "now-3M/d", "to": "now/d", "key": "최근 3개월"}
                ]
            }
        }
    }

# --- 외부 호출용 메인 함수 ---

def build_search_query(query_params: SearchQuery) -> Dict[str, Any]:
    """
    SearchQuery 모델을 받아 Elasticsearch DSL 쿼리 객체를 생성
    - filter: 기관, 카테고리, 유형, 날짜
    - must: 검색어 (multi_match)
    - sort: 정렬 방식
    - pagination: from/size
    - highlight: title, summary 강조
    - aggregations: 필터 조건에 대한 통계 제공
    """
    try:
        # 각 쿼리 절 생성
        filters = _build_filter_clause(query_params)
        must_clause = _build_must_clause(query_params.q)
        sort_clause = _build_sort_clause(query_params.sort)
        aggregations = _build_aggregations()

        # 페이지네이션 처리(from: 시작위치, size: 페이지 크기)
        from_offset = (query_params.page - 1) * query_params.limit

        return {
            "query": {"bool": {"must": must_clause, "filter": filters}},
            "from": from_offset,
            "size": query_params.limit,
            "sort": sort_clause,
            "highlight": {
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"],
                "fields": {"title": {}, "summary": {}}
            },
            "aggs": aggregations,
        }
    except Exception as e:
        logger.error(f"Failed to build search query with params: {query_params.dict()}", exc_info=True)
        # 쿼리 빌드 중 발생한 오류는 내부 로직 오류일 가능성이 높으므로,
        # 에러를 그대로 던져 search_contents가 잡아서 처리하도록 합니다.
        raise ValueError(f"Failed to build search query: {e}")