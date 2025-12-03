// frontend_app/app/documents/[docId]/page.js

'use client';

import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { getDocumentContext, getSegmentDetail, getPdfPreviewUrl } from '../../../utils/api'; 
import DetailView from '../components/DetailView'; 

export default function DocumentDetailPage() {
  const params = useParams();
  const docId = params.docId; 
  
  const searchParams = useSearchParams();
  // 검색 결과에서 클릭된 세그먼트의 ID (강조 및 스크롤 위치 지정용)
  const initialSegmentId = searchParams.get('segmentId'); 

  const [documentData, setDocumentData] = useState(null);
  const [segmentData, setSegmentData] = useState(null); // 클릭된 세그먼트 상세 정보
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!docId || !initialSegmentId) {
        setError("필수 문서 ID 또는 세그먼트 ID가 누락되었습니다.");
        setLoading(false);
        return;
    }

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // 1. 전체 문서 문맥 로드 (모든 세그먼트 포함)
        const docContextPromise = getDocumentContext(docId);
        
        // 2. 초기 세그먼트 상세 정보 로드 (page_number 등 빠른 정보 확인용)
        const segmentDetailPromise = getSegmentDetail(initialSegmentId);

        // 병렬 호출
        const [docData, segData] = await Promise.all([
          docContextPromise,
          segmentDetailPromise
        ]);

        setDocumentData(docData);
        setSegmentData(segData);
        
      } catch (err) {
        console.error("Detail Fetch Error:", err);
        setError(err.message || "상세 정보 로드 중 오류가 발생했습니다.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [docId, initialSegmentId]);

  // 로딩 및 오류 처리 UI
  if (loading) {
    return <div className="p-8 text-center text-xl text-blue-600">회의록 문맥을 불러오는 중...</div>;
  }
  if (error || !documentData) {
    return <div className="p-8 text-center text-red-600 font-bold">{error || "문서를 찾을 수 없습니다. (404)"}</div>;
  }
  
  // 성공 시 3단계 컴포넌트 렌더링
  return (
    <DetailView 
      documentData={documentData}
      segmentData={segmentData} 
      initialSegmentId={initialSegmentId}
      pdfUrl={getPdfPreviewUrl(docId)} 
    />
  );
}