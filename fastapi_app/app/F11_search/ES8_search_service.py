# app/F11_search/ES8_search_service.py

import logging
import math
from time import perf_counter
from typing import Dict, Any, List, Union
from elasticsearch.exceptions import ConnectionTimeout

from app.F5_core.config import settings
from app.F6_schemas.base import ErrorResponse, ErrorDetail, ErrorCode

# Elasticsearch 비동기 클라이언트 인스턴스
from app.F11_search.ES1_client import es_async

# 검색 쿼리 DSL을 동적으로 생성하는 함수
from app.F11_search.ES7_query_builder import build_search_query

# 검색 API의 요청 및 응답 스키마 및 에러 코드 정의
from app.F6_schemas.search import (
    SearchQuery,                # 검색 요청 쿼리 파라미터
    SearchResponse,             # 최종 API 응답 스키마
    SearchResultItem,           # 개별 검색 결과 아이템
    SearchData,                 # 응답의 실제 데이터 묶음
    SearchPagination,           # 페이지네이션 정보
    SearchAggregations,         # 집계 정보
    AggregationItem,            # 각 집계 항목
    SearchOrganization,         # 결과 내 조직 정보
    SearchCategory,             # 결과 내 카테고리 정보
    SearchHighlight             # highlight 결과 포맷
)

logger = logging.getLogger(__name__)

# --- 내부 헬퍼 함수 (변경 없음) ---
def _format_search_results(hits: List[Dict[str, Any]]) -> List[SearchResultItem]:
    """
    Elasticsearch 결과에서 hits(_source, highlight등)를 추출
    SearchResultItem 리스트로 변환
    """

    results = []
    for hit in hits:
        source = hit.get("_source", {})         # 원본 데이터
        highlight_data = hit.get("highlight", {})   # highlight된 필드
        org_source = source.get("organization", {}) or {}
        cat_source = source.get("category", {}) or {}

        item = SearchResultItem(
            id=int(source.get("id", 0)),
            title=source.get("title", ""),
            summary=source.get("summary", ""),
            organization=SearchOrganization(
                id=org_source.get("id"),
                name=org_source.get("name"),
                logo_url=org_source.get("logo_url")
            ),
            category=SearchCategory(
                id=cat_source.get("id"),
                name=cat_source.get("name")
            ),
            type=source.get("type", ""),
            published_date=source.get("published_date"),
            view_count=source.get("view_count", 0),
            average_rating=source.get("average_rating", 0.0),
            bookmark_count=source.get("bookmark_count", 0),
            url=source.get("url", ""),
            highlight=SearchHighlight(
                title=''.join(highlight_data.get("title", [source.get("title", "")])),
                summary=''.join(highlight_data.get("summary", [source.get("summary", "")]))
            )
        )
        results.append(item)
    return results

def _format_aggregations(aggregations_data: Dict[str, Any]) -> SearchAggregations:
    """
    Elasitcsearch 집계 결과(aggregations)를 SearchAggregations 모델로 변환
    """
    def format_buckets(agg_name):
        buckets = aggregations_data.get(agg_name, {}).get("buckets", [])
        return [AggregationItem(name=b.get("key"), count=b.get("doc_count")) for b in buckets]
    
    return SearchAggregations(
        organizations=format_buckets("organizations"),
        categories=format_buckets("categories"),
        types=format_buckets("types"),
        date_ranges=format_buckets("date_ranges")
    )


# --- 외부 호출용 메인 함수 (최종 수정 완료) ---
async def search_contents(query_params: SearchQuery) -> Union[SearchResponse, ErrorResponse]:
    """
    사용자 검색 요청을 받아 Elasticsearch에서 검색을 수행
    - 성공: SearchResponse 반환
    - 실패: ErrorResponse 반환
    """
    # 성능 측정 시작 시간 기록
    start_time = perf_counter()

    try:
        # Elasticsearch 클라이언트 유효성 검사
        if not es_async:
            logger.error("Asynchronous Elasticsearch client is not available.")
            raise RuntimeError("Asynchronous Elasticsearch client is not available.")

        # --- [1] 검색 DSL 생성 (← ES7_query_builder.py 사용) ---
        es_query = build_search_query(query_params)
        logger.debug(f"Elasticsearch Query: {es_query}")

        # --- [2] Elasticsearch 검색 실행 ---
        response = await es_async.search(
            index=settings.ELASTICSEARCH_READ_ALIAS,
            body=es_query,
            request_timeout=10 # 검색 제한 시간 (초)
        )

        # --- [3] 검색 결과 처리 ---
        hits = response.get("hits", {}).get("hits", [])
        total_count = response.get("hits", {}).get("total", {}).get("value", 0)
        
        results = _format_search_results(hits) # 검색 결과 목록 포맷
        aggregations = _format_aggregations(response.get("aggregations", {}))
        
        # 페이지네이션 계산
        total_pages = math.ceil(total_count / query_params.limit) if query_params.limit > 0 else 0
        pagination = SearchPagination(
            current_page=query_params.page,
            total_pages=total_pages,
            total_count=total_count,
            limit=query_params.limit,
            has_next=query_params.page < total_pages,
            has_previous=query_params.page > 1
        )

        # 전체 검색 시간 계산
        search_time_str = f"{perf_counter() - start_time:.4f}s"

        # --- [4] 최종 데이터 조립 ---
        search_data = SearchData(
            query={
                "keyword": query_params.q,
                "filters": {
                    "organizations": query_params.organizations.split(',') if query_params.organizations else [],
                    "categories": query_params.categories.split(',') if query_params.categories else [],
                    "types": query_params.types.split(',') if query_params.types else [],
                    "date_range": {
                        "from": query_params.date_from,
                        "to": query_params.date_to
                    }
                },
                "sort": query_params.sort
            },
            results=results,
            pagination=pagination,
            aggregations=aggregations,
            search_time=search_time_str
        )
        return SearchResponse(success=True, data=search_data)

    # --- [5] 예외 처리 ---

    except ConnectionTimeout:
        # Elasticsearch 응답 시간 초과
        logger.warning(f"Search timed out for query: {query_params.dict()}", exc_info=True)
        return ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.SEARCH_TIMEOUT,
                message="검색 요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
            )
        )

    except Exception as e:
        # 그 외 예기치 못한 에러
        logger.error(f"An unexpected internal error occurred during search: {query_params.dict()}", exc_info=True)
        return ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.INTERNAL_ERROR,
                message="요청을 처리하는 중 서버에 예기치 않은 오류가 발생했습니다."
            )
        )