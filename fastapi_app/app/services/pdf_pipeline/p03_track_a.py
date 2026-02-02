import asyncio

from keybert import KeyBERT
from kiwipiepy import Kiwi
from collections import Counter
from typing import List 
from sentence_transformers import SentenceTransformer

from app.models.document_processes import ProcessStatus
from app.repositories.pdf_process.p03_track_a import PdfKeywordExtractorRepository
from app.utils.stopwords import STOP_WORDS

from app.schema.pdf import DocumentPageSegmentsSchema, DocumentSegmentSaveSchema
from app.core.config import settings


# ============================================================
# Track A - PDF 발언 세그먼트 기반 키워드 추출 서비스
# ------------------------------------------------------------
# [제목]
# PdfKeywordExtractorService
#
# [목적]
# 2단계에서 생성된 발언 세그먼트 데이터를 기반으로
# 각 발언 단위별 핵심 키워드를 자동 추출하여
# 검색/요약/분석에 활용 가능한 구조화 데이터를 생성한다.
#
# [핵심 동작]
# - PARSED 상태의 문서 세그먼트 데이터 조회
# - CPU-bound 키워드 추출 작업을 asyncio.to_thread로 비동기 처리
# - Kiwi 형태소 분석 기반 명사 후보 추출 후 KeyBERT 적용
# - 세그먼트 단위 키워드 결과를 DB에 저장하고 상태 갱신
# ============================================================



# ============================================================
# PdfKeywordExtractorService
# ------------------------------------------------------------
# [제목]
# PDF 발언 세그먼트 기반 키워드 추출 서비스 클래스
#
# [목적]
# DocumentPageSegmentsSchema 구조의 발언 데이터를 입력받아
# 각 발언 단위별 대표 키워드를 추출하고 DB 저장용 DTO로 변환한다.
#
# [핵심 동작]
# - Kiwi + KeyBERT 기반 키워드 추출 파이프라인 제공
# - asyncio.to_thread를 통한 CPU-bound 병렬 처리 지원
# - 추출 결과를 DocumentSegmentSaveSchema 구조로 변환
# ============================================================
class PdfKeywordExtractorService:
    def __init__(self, 
                db_p03_track_a: PdfKeywordExtractorRepository,
                kiwi_instance: Kiwi, 
                embedding_model: SentenceTransformer,
                keybert_model: KeyBERT
        ):
        self.db_repo = db_p03_track_a
        self.kiwi = kiwi_instance
        self.embedding_model = embedding_model 
        self.kw_model = keybert_model 
        self.stop_words = STOP_WORDS


    # ------------------------------------------------------------
    # [메인 함수] 발언 세그먼트 기반 키워드 추출 파이프라인
    # ------------------------------------------------------------
    # [목적]
    # PARSED 상태의 문서 세그먼트 데이터를 조회하여
    # 각 발언 단위별 키워드를 비동기로 추출하고 DB에 저장한다.
    #
    # [핵심 동작]
    # 1. 키워드 추출 대상 프로세스 조회
    # 2. JSON → Pydantic 스키마 변환
    # 3. asyncio.to_thread로 CPU-bound 키워드 추출 실행
    # 4. 결과를 세그먼트 테이블에 저장
    # 5. 프로세스 상태 KEYWORD로 갱신 및 커밋
    # ------------------------------------------------------------
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
                save_dtos = await asyncio.to_thread(
                    self._process_single_document, 
                    document_id, 
                    process_id, 
                    input_data
                )

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

    # ------------------------------------------------------------
    # [보조 함수] 단일 문서 세그먼트 키워드 추출 처리기
    # ------------------------------------------------------------
    # [목적]
    # 하나의 문서(Page → Segment 구조)를 순회하며
    # 각 발언 단위별 키워드를 추출하고 저장용 DTO 리스트를 생성한다.
    #
    # [핵심 동작]
    # - 모든 페이지/세그먼트 순회
    # - 길이 기준 필터링 후 키워드 추출 실행
    # - DocumentSegmentSaveSchema 형태로 평탄화(flatten) 변환
    # ------------------------------------------------------------
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
                # 너무 짧은 문장 스킵
                if len(text) <= 15: continue 

                # 키워드 추출 로직 
                keywords = self._extract_keywords_bert(text)

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
    

    # ------------------------------------------------------------
    # [보조 함수] KeyBERT + Kiwi 기반 키워드 추출 로직
    # ------------------------------------------------------------
    # [목적]
    # 한국어 문장에 대해 KeyBERT 성능을 개선하기 위해
    # Kiwi 형태소 분석으로 명사 후보만 추출한 뒤 키워드를 생성한다.
    #
    # [핵심 동작]
    # - Kiwi로 일반명사/고유명사(NNG, NNP)만 필터링
    # - 불용어 제거 후 명사 나열 텍스트 생성
    # - KeyBERT(MMR 옵션)로 상위 키워드 추출
    # - ['키워드1', '키워드2', ...] 형태로 반환
    # ------------------------------------------------------------
    def _extract_keywords_bert(self, text: str, top_n: int = 5) -> List[str]:
        """
        KeyBERT를 사용하되, 명사 단위로 후보를 좁혀서 추출 품질 향상
        """

        try: 
            # 1. Kiwi로 명사만 추출하여 공백으로 연결(전처리)
            # 이유: KeyBERT는 띄어쓰기 기준으로 토큰을 나누는데, 한국어는 조사 때문에 바로 넣으면 성능 저하
            nouns = []
            tokens = self.kiwi.analyze(text, normalize_coda=True)
            for token in tokens[0][0]:
                if token.tag in ['NNG', 'NNP']: # 일반명사, 고유명사
                    word = token.form 
                    if len(word) > 1 and word not in self.stop_words: 
                        nouns.append(word)
            
            if not nouns:
                return []
        
            # 명사들로만 구성된 텍스트를 만듦
            candidate_text = " ".join(nouns)


            # 2. KeyBERT 실행
            # keyphrase_ngram_range(1, 1): 1단어짜리 키워드 추출(필요하면(1, 2)로 복합명사 추출 가능)
            # use_mmr=True: 다양성 있는 키워드 추출(중복 의미 방지)
            keywords = self.kw_model.extract_keywords(
                docs=candidate_text, # 원문 대신 명사 나열 텍스트 삽입
                keyphrase_ngram_range=(1, 1), 
                stop_words=None, # 이미 위에서 걸러냄
                top_n=top_n,
                use_mmr=True,    # Maximal Marginal Relevance (다양성 확보)
                diversity=0.3    # 0.3 정도가 적당 (높을수록 다양한 단어, 낮을수록 대표성 강한 단어)
            )

            # 결과 포맷: [('키워드', 0.82), ('단어', 0.75)] -> ['키워드', '단어']
            return [k[0] for k in keywords]
        except Exception as e:
            print(f"KeyBERT Error: {e}")
            return []
    
