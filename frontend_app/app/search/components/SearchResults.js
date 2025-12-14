// frontend_app/app/search/components/SearchResults.js

import React from 'react';
import Link from 'next/link'; 

export default function SearchResults({ data }) {
  if (!data || data.total_hits === 0) return null;

  return (
    <div className="space-y-6">
      {data.results.map((item, index) => (
        <Link 
          key={item.segment_id} 
          href={`/document/${item.doc_id}?segmentId=${item.segment_id}`}
          className="block p-4 border-b border-gray-100 hover:bg-blue-50 transition duration-150 bg-white group"
        >
          
          {/* 1. 문서 제목 (가장 눈에 띄게) */}
          {/* 백엔드에서 title 필드가 넘어온다고 가정 */}
          <h3 className="text-lg font-medium text-blue-800 mb-1 group-hover:underline">
            {item.title || "제목 없음"} 
          </h3>
          
          {/* 2. 메타 정보 (위원회, 날짜, 발언자) */}
          <div className="text-xs text-gray-500 mb-2 flex items-center space-x-3">
            
            {/* 위원회 (위원 황정아 왼쪽에 배치) */}
            <span className="text-gray-600 font-semibold">{item.committee_name || '위원회 정보 없음'}</span>
            
            <span>|</span>
            
            {/* 회의 날짜 */}
            <span className="text-gray-500">{item.conf_date}</span>

            <span>|</span>
            
            {/* 발언자 정보 */}
            <span className="text-gray-700 font-medium">발언자: {item.speaker}</span>
          </div>
          
          {/* 3. 하이라이트된 스니펫 */}
          <p 
            className="text-base text-gray-900 line-clamp-3 my-2"
            dangerouslySetInnerHTML={{ __html: item.highlight }} 
          />
          
          {/* 4. 키워드 태그 */}
          {item.keywords && (
            <div className="mt-2 text-xs">
              {item.keywords.map(kw => (
                <span key={kw} className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded mr-1">
                  {kw}
                </span>
              ))}
            </div>
          )}
        </Link>
      ))}
    </div>
  );
}