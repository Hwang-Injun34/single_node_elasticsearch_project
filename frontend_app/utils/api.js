// frontend_app/utils/api.js

// const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL; 
const BASE_URL = "http://localhost:";  // 운영환경에서는 환경변수로 설정 필요
// FastAPI 라우터에서 사용되는 버전 경로
const API_VERSION_PATH = "/api/v1"; 

if (!BASE_URL) {
  // 환경 변수 검사
  console.error("VITE_API_BASE_URL environment variable is not set.");
  // Next.js (Webpack) 환경에서는 VITE_ 대신 NEXT_PUBLIC_ 접두사를 사용할 수도 있습니다.
  // 실제 Next.js 설정에 따라 process.env.NEXT_PUBLIC_API_BASE_URL 로 변경이 필요할 수 있습니다.
}

/**
 * 기본 API fetch 유틸리티 함수
 * @param {string} endpoint - /search, /documents/doc_123 등 (버전 경로 제외)
 * @param {object} options - fetch 옵션 (method, headers 등)
 */
export async function apiFetch(endpoint, options = {}) {
  const url = `${BASE_URL}${API_VERSION_PATH}${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!response.ok) {
    // API 오류 시 JSON 상세 정보 추출 및 Throw
    let errorDetail = { detail: 'API Request Failed' };
    try {
        errorDetail = await response.json();
    } catch (e) {
        // JSON 파싱 실패 시, HTTP 상태 텍스트 사용
        throw new Error(`API Request Failed: ${response.statusText} (${response.status})`);
    }
    throw new Error(errorDetail.detail || `API Request Failed: ${response.statusText} (${response.status})`);
  }

  // 파일 응답(PDF)이 아닌 경우 JSON을 반환
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return response.json();
  }
  
  // JSON이 아니면, 응답 객체 자체를 반환 (호출하는 쪽에서 .text() 또는 .blob()을 처리해야 할 수 있음)
  return response; 
}


// ------------------- 1. Search API -------------------

/**
 * [GET /api/v1/search] 검색 결과 목록을 가져옵니다.
 * @param {string} keyword - 검색어
 * @param {number} limit - 결과 개수 제한
 * @returns {SearchResponse}
 */
export async function searchMinutes(keyword, limit = 20) {
  const params = new URLSearchParams({ 
    q: keyword, 
    limit: limit 
  }).toString();
  
  return apiFetch(`/search?${params}`);
}

// ------------------- 2. Detail / Context APIs -------------------

/**
 * [GET /api/v1/documents/{docId}] 전체 문서 문맥과 세그먼트 리스트를 가져옵니다.
 * @param {string} docId
 * @returns {DocumentDetail}
 */
export async function getDocumentContext(docId) {
  return apiFetch(`/document/${docId}`);
}

/**
 * [GET /api/v1/segments/{segmentId}] 특정 세그먼트의 상세 정보를 빠르게 가져옵니다.
 * @param {string} segmentId
 * @returns {SegmentDetail}
 */
export async function getSegmentDetail(segmentId) {
  return apiFetch(`/segment/${segmentId}`);
}

// ------------------- 3. PDF Preview API URL -------------------

/**
 * [GET /api/v1/documents/{docId}/pdf] PDF 파일 스트리밍 엔드포인트의 URL을 생성합니다.
 * (이 함수는 파일을 직접 fetch하지 않고, iframe 등에 사용될 URL만 반환합니다.)
 * @param {string} docId
 * @returns {string} PDF 파일 URL
 */
export function getPdfPreviewUrl(docId) {
    // PDF 경로는 API 버전 경로를 포함한 절대 주소를 반환합니다.
    return `${BASE_URL}${API_VERSION_PATH}/document/${docId}/pdf`;
}