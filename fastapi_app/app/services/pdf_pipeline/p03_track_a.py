import asyncio

from kiwipiepy import Kiwi
from collections import Counter
from typing import List 

from app.models.document_processes import ProcessStatus
from app.repositories.pdf_process.p03_track_a import PdfKeywordExtractorRepository
from app.utils.stopwords import STOP_WORDS

from app.schema.pdf import DocumentPageSegmentsSchema, DocumentSegmentSaveSchema


# ===============================
# 3단계_TrackA: 키워드 추출
# ===============================
# 비동기로
# 1. 대상 조회
# 2. 구조 스키마를 통해 그형태를 가지고 
# 3. 하나의 page_local_id를 뽑아냄
# 4. 키워드 추출
# 5. 데이터 저장 
# 비동기로 추출되면 좋겠음


class PdfKeywordExtractorService:
    def __init__(self, db_p03_track_a: PdfKeywordExtractorRepository):
        self.db_repo = db_p03_track_a
        self.kiwi = Kiwi()
        self.stop_words = STOP_WORDS

    # -------------------------
    #       [메인 함수]
    # -------------------------
    async def run_keyword_extraction(self, limit: int=3):
        """
        DB에서 대상 조회 -> 비동기 키워드 추출 -> DB 업데이트
        """
        # -- [Step 1] 대상 조회 (PARSED 완료된 건들) --
        targets = await self.db_repo.get_speaker_texts(limit)

        if not targets:
                print("처리할 PDF가 없음")
                return 

        print("---------- [Track A] 키워드 추출 결과 ----------")

        processed_count = 0

        for row in targets:
            try:
                # -- [Step 2] JSON 데이터 가져오기
                raw_json = row.content.speaker_segments
                document_id = row.document_id
                process_id = row.id 

                if not raw_json:
                    print(f"Document ID {document_id}: segments 데이터가 비어있습니다. [Skip]")
                    continue
                
                # Pydantic으로 검증 및 객체화
                input_data = DocumentPageSegmentsSchema(**raw_json)

                # -- [Step 3] 비동기 키워드 추출 실행(CPU Bound 작업) --
                # 별도 스레드에서 _process_document 실행
                save_dtos = await asyncio.to_thread(self._process_single_document, document_id, process_id, input_data)

                # -- [Step 4] DB 저장 (세그먼트 테이블 Insert) --
                # 데이터를 저장할 때 이제는 DocumentSegment에 저장하기 때문에 Documnet 만 동일하고 
                # 화자가 말한거 따로 저장할 계획
                await self.db_repo.save_keyword_result(document_id, save_dtos)

                # 상태 업데이트
                await self.db_repo.update_process_status(process_id, ProcessStatus.KEYWORD)

                processed_count += 1
                print(f"Document ID {document_id} 완료 ({len(save_dtos)} segments)")

            except Exception as e:
                print(f"Document ID {document_id} 처리 중 오류: {e}")
                await self.db_repo.update_process_status(process_id, ProcessStatus.FAILED)
        
        # -- [Step 5] 최종 커밋 --
        if processed_count > 0:
            await self.db_repo.commit()
            print(f"총 {processed_count}건 처리 완료.")

    # -------------------------
    #       [보조 함수]
    # -------------------------
    def _process_single_document(self, document_id: int, process_id: int, input_data: DocumentPageSegmentsSchema) -> List[DocumentSegmentSaveSchema]:
        """
        [CPU Bound]
        1. JSON 구조(Page -> Segment)를 순회하며
        2. 키워드 추출 수행
        3. 저장용 DTO(Flat 구조) 리스트 생성
        """
        result_list = []

        for page in input_data.pages:
            for seg in page.segments:
                text = seg.text.strip()
                if not text: continue 

                # 키워드 추출 로직 
                keywords = self._extract_keywords(text)

                # 저장용 스키마 생성(Flatten)
                dto = DocumentSegmentSaveSchema(
                    document_id=document_id,
                    process_id=process_id,
                    page_number=page.page,
                    speaker_name=seg.speaker_name,
                    speaker_role=seg.speaker_role,
                    original_text=text,
                    keywords=keywords
                )

                result_list.append(dto)
        print(result_list)
        return result_list
    
    def _extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """
        순수 키워드 추출 로직
        - 텍스트 -> 명사 추출 -> 상위 N개 반환
        """

        # 최소 길이 방어 로직
        # "네", "아니오" 같은 너무 짧은 문장은 분석할 가치가 없음
        if not text or len(text) < 5: return []
        
        # Kiwi 분석
        # normalize_code = True: "했읍니다." -> "했습니다." 같이 옛날 말이나 오타를 잡음
        result = self.kiwi.analyze(text, normalize_coda=True)
        nouns = []

        # 분석 결과 하나씩 뜯기
        # result[0][0]은 kiwi 라이브러리 특유의 결과 접근 방식
        for token in result [0][0]:
            # [필터 1] 품사(POS)가 명사인가?
            # NNG: 일반 명사 (예: 학교, 의사)
            # NNP: 고유 명사 (예: 대한민국, 이재명)
            if token.tag in ['NNG', 'NNP']:

                # [필터 2] 쓸모있는 명사인가?
                # len(token.form) > 1 : '것', '수', '등' 같은 1글자 의존명사는 보통 검색에 도움 안됨
                # not in self.stop_words: '위원장', '말씀' 같이 너무 뻔한 단어 제외
                if len(token.form) > 1 and token.form not in self.stop_words:
                    nouns.append(token.form)

        # 빈도수 세기
        # Counter가 리스트 안의 단어 개수를 세준다.
        # most_common(top_n): 가장 많이 나온 순서대로 N개만 
        return [word for word, _ in Counter(nouns).most_common(top_n)]

