// frontend_app/app/documents/components/DetailView.js (수정된 코드)

import React, { useRef, useEffect } from 'react';
import Link from 'next/link';
import SegmentRenderer from './SegmentRenderer';
import PdfViewer from './PdfViewer'; 

export default function DetailView({ 
    documentData, 
    segmentData, 
    initialSegmentId, 
    pdfUrl 
}) {
  const segmentsRef = useRef({}); 
  // 💡 containerRef는 스크롤을 실제로 담당하는 내부 div에 연결해야 합니다.
  const scrollAreaRef = useRef(null); 

  // 3.3 자동 스크롤 및 강조 로직 (페이지 로드 후 실행)
  useEffect(() => {
    const element = segmentsRef.current[initialSegmentId];
    const scrollContainer = scrollAreaRef.current;
    
    if (element && scrollContainer) {
      
      // 1. 해당 요소로 부드럽게 스크롤
      // element.offsetTop: 요소가 스크롤 컨테이너 상단에서 얼마나 떨어져 있는지 (상대적 위치)
      // 스크롤 위치를 해당 요소의 상단으로 이동시키되, 50px 여유를 줍니다.
      const scrollPosition = element.offsetTop - 50; 
      
      scrollContainer.scrollTo({
        top: scrollPosition,
        behavior: 'smooth', 
      });
      
      // 2. 시각적 강조 클래스 추가
      element.classList.add('highlight-segment'); 
      
      const timer = setTimeout(() => {
          element.classList.remove('highlight-segment');
      }, 5000); 

      return () => clearTimeout(timer); 
    }
  }, [initialSegmentId, documentData]); 

  const docMeta = documentData;
  const initialPageNumber = segmentData?.page_number || 1;
  
  return (
    <div className="flex max-w-screen-xl mx-auto p-4 h-screen bg-gray-50">
        
      {/* 1. 좌측: 회의록 본문 전체 (문맥 뷰) */}
      <div 
        className="w-1/2 flex flex-col overflow-hidden bg-white border border-gray-200 rounded-l-lg shadow-xl"
      >
        {/* 헤더 메타정보 고정 */}
        <div className="p-4 border-b bg-gray-50 sticky top-0 z-10">
            <Link href="/search" className="text-blue-600 hover:text-blue-800 text-sm">
                ← 검색 결과로 돌아가기
            </Link>
            <h1 className="text-xl font-bold mt-2 text-blue-800">{docMeta.title}</h1>
            <p className="text-sm text-gray-600">
                {docMeta.committee_name} | 회의일: {docMeta.confDate}
            </p>
        </div>

        {/* 세그먼트 렌더링 영역 (스크롤 컨테이너) */}
        <div 
            ref={scrollAreaRef} /* 💡 스크롤을 담당하는 div에 Ref 연결 */
            className="flex-grow overflow-y-auto p-6 space-y-5"
        >
            {docMeta.segments.map((segment) => (
              <SegmentRenderer
                key={segment.id}
                segment={segment}
                isHighlighted={segment.id === initialSegmentId}
                ref={(el) => segmentsRef.current[segment.id] = el}
              />
            ))}
        </div>
      </div>

      {/* 2. 우측: PDF 미리보기 (고정) */}
      <div className="w-1/2 p-4 bg-gray-100 border border-gray-200 rounded-r-lg shadow-xl">
        <h2 className="text-lg font-semibold mb-3 border-b pb-2">원본 PDF 미리보기</h2>
        <PdfViewer 
          pdfUrl={pdfUrl} 
          initialPage={initialPageNumber}
          docTitle={docMeta.title}
        />
      </div>
      
      {/* 🚨 CSS 설정은 이전과 동일 */}
    </div>
  );
}