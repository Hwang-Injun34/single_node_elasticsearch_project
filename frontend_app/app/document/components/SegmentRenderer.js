import React, { forwardRef } from 'react';

// forwardRef를 사용하여 부모 컴포넌트(DetailView)가 DOM 요소에 접근할 수 있게 함
const SegmentRenderer = forwardRef(({ segment, isHighlighted }, ref) => {
  return (
    <div 
      ref={ref} 
      className={`p-3 rounded-lg border transition duration-300 
                  ${isHighlighted ? 'bg-yellow-50 border-yellow-300 shadow-md' : 'bg-white border-gray-100'}`}
      id={`segment-${segment.id}`} // DOM ID 설정
    >
      <div className="flex justify-between text-xs text-gray-600 mb-1">
        <span className="font-semibold">{segment.speaker_role} {segment.speaker_name}</span>
        <span>Page {segment.page_number}</span>
      </div>
      <p className="text-sm whitespace-pre-wrap text-gray-900">{segment.original_text}</p>
    </div>
  );
});

SegmentRenderer.displayName = 'SegmentRenderer'; // 디버깅을 위한 displayName
export default SegmentRenderer;