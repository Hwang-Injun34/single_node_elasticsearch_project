import React from 'react';

export default function PdfViewer({ pdfUrl, initialPage, docTitle }) {
  // 💡 PDF URL에 페이지 번호 앵커를 추가하여 브라우저가 해당 페이지로 이동하도록 유도
  // 브라우저에 따라 작동 방식이 다를 수 있지만, 가장 기본적인 방법입니다.
  const viewerUrl = `${pdfUrl}#page=${initialPage}`;

  // PDF 다운로드 링크
  const downloadUrl = `${pdfUrl}`;

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-end mb-2">
        <a 
          href={downloadUrl} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:underline"
        >
          [원본 PDF 다운로드]
        </a>
      </div>
      
      {/* iframe을 사용하여 브라우저 내장 뷰어로 렌더링 */}
      <iframe 
        src={viewerUrl} 
        title={`${docTitle} PDF Preview`}
        className="flex-grow w-full border border-gray-300 rounded-lg"
        allowFullScreen
      />
    </div>
  );
}