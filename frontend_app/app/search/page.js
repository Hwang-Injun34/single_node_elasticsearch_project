// frontend_app/app/search/page.js

'use client'; 

import { useState } from 'react';
// utils/api.js에서 정의된 API 호출 함수
import { searchMinutes } from '../../utils/api'; 
// 하위 컴포넌트 import
import SearchForm from './components/SearchForm'; 
import SearchResults from './components/SearchResults'; 

// 이 함수 이름(SearchPage)이 컴포넌트 이름이지만, 파일명은 page.js 입니다.
export default function SearchPage() {
  const [keyword, setKeyword] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (kw) => {
    // 쿼리 파라미터로 사용할 수 있도록 공백 제거 후 저장
    const trimmedKw = kw.trim();
    if (!trimmedKw) return;

    setKeyword(trimmedKw);
    setLoading(true);
    setError(null);
    setResults(null); 

    try {
      const data = await searchMinutes(trimmedKw);
      setResults(data); 
    } catch (err) {
      console.error("Search Error:", err);
      // API 유틸리티에서 던진 오류 메시지 사용
      setError(err.message || "검색 중 알 수 없는 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    // 배경: 흰색, 최소 높이: 화면 전체
    <div className="min-h-screen bg-white text-gray-800">
      
      {/* -------------------- 1. 검색 헤더/폼 영역 -------------------- */}
      <div className="flex flex-col items-center pt-24 pb-12 w-full max-w-2xl mx-auto px-4">
        
        {/* 제목: 신뢰감 있는 색상과 폰트 */}
        <h1 className="text-5xl font-extrabold text-blue-800 mb-2 tracking-tight">
          PolitiSearch
        </h1>
        <p className="text-lg text-gray-600 mb-8">국회 회의록 하이브리드 검색 시스템</p>

        {/* 검색 폼 컴포넌트 */}
        <SearchForm onSearch={handleSearch} isLoading={loading} />
      </div>

      {/* -------------------- 2. 결과 표시 영역 -------------------- */}
      {results && results.total > 0 && (
          // 결과가 있을 때만 결과 영역을 표시
          <div className="w-full max-w-2xl mx-auto px-4 pb-12">
            
            {/* 통계 정보 */}
            <p className="text-sm text-gray-500 mb-4 border-b pb-2">
              총 {results.total}건의 결과 ({results.took.toFixed(2)}초)
            </p>
            
            {/* 결과 리스트 컴포넌트 */}
            <SearchResults data={results} />
          </div>
      )}
      
      {/* -------------------- 3. 상태 및 오류 메시지 -------------------- */}
      <div className="w-full max-w-2xl mx-auto px-4 mt-4 text-center">
          {loading && <p className="text-blue-500">검색 중입니다. 잠시만 기다려 주세요...</p>}
          {error && <p className="text-red-500 font-medium">❌ 오류 발생: {error}</p>}
          {results && results.total === 0 && !loading && !error && (
            <p className="text-gray-600">검색 결과가 없습니다. 다른 키워드를 시도해보세요.</p>
          )}
      </div>

    </div>
  );
}