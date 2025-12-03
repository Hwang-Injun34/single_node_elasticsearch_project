// frontend_app/app/search/components/SearchForm.js (수정)

import React, { useState } from 'react';

export default function SearchForm({ onSearch, isLoading }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(input);
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col w-full">
      <div className="flex items-center border border-gray-300 rounded-full shadow-md hover:shadow-lg focus-within:shadow-xl transition duration-300 overflow-hidden">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="검색어를 입력하세요..."
          className="flex-grow p-3 pl-6 text-lg border-none focus:ring-0 focus:outline-none"
          disabled={isLoading}
        />
        <button
          type="submit"
          className={`p-4 transition duration-150 ${
            isLoading ? 'text-gray-400' : 'text-blue-600 hover:text-blue-800'
          }`}
          disabled={isLoading}
        >
          {/* 돋보기 아이콘 (Tailwind CSS와 함께 사용할 수 있는 Heroicons 가정) */}
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        </button>
      </div>

      {/* 버튼은 숨기고, 엔터를 주로 사용하도록 유도 (구글 스타일)
      {/* 추가적인 행동 버튼이 필요하다면 여기에 배치할 수 있습니다. */}
    </form>
  );
}