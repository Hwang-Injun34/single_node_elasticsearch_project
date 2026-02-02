import re
import zlib
import json
from typing import Tuple, List

from app.repositories.pdf_process.p02_pdf_transcript_parser import PdfTranscriptParserRepository
from app.models.document_processes import ProcessStatus
from app.schema.pdf import (
    PageTextSchema, 
    DocumentPageSegmentsSchema,
    PageSegmentsSchema,
    SegmentSchema,
    TotalPageTextSchema
)

# ============================================================
# PdfTranscriptParserService
# ------------------------------------------------------------
# [제목]
# PDF 회의록 텍스트 → 발언 단위(segments) 구조화 서비스
#
# [목적]
# 1단계에서 추출된 PDF 페이지 텍스트를 분석하여
# 화자별 발언 단위(segment)로 분리하고,
# 페이지/화자/직책/발언 내용을 구조화된 스키마로 저장한다.
#
# [핵심 동작]
# - 머리말, 의사일정, 종료 문구 등 불필요한 라인 제거
# - ◯ 기호 기반 화자 발언 감지 및 화자/직책/내용 파싱
# - 페이지 단위 SegmentSchema 리스트 생성
# - 결과를 DB에 저장하고 처리 상태를 PARSED로 갱신
# ============================================================
class PdfTranscriptParserService:
    def __init__(self, db_p02: PdfTranscriptParserRepository):
        self.db_repo = db_p02

        # 정규식 패턴
        self.SPEAKER_RE = re.compile(r"^\s*[◯Oㅇ0]\s*(?P<Line>.*)")
        self.STOP_PATTERN = re.compile(r"\d{1,2}시\d{1,2}분\s*산회")

        # 머리말(Header) 패턴
        self.HEADER_RE = re.compile(
            r"^\s*(\d+\s+)?제\s*\d+\s*회.*\(.*\d+년.*\d+월.*\d+일\)(\s+\d+)?\s*$"
        )

        # 의사 일정 식별: 숫자 + 안건명 + 의안번호
        self.AGENDA_RE = re.compile(
            r"^\s*\d+[\.\s]\s*.*"                   # 숫자. 으로 시작
            r"(?:법률안|의안|안건|건|특별법안|보고)"   # 필수 키워드
            r"(?:\(.*\d+\)?|(?:\s*\(대안\)))?"       # (의안번호) 또는 (대안) 등 (선택사항)
        )

        # 집단 응답 및 상황 묘사
        self.COLLECTIVE_RE = re.compile(r"^\s*\([「]?.*[」]?\s*(?:하는\s*(?:위원|의원)(?:들)?\s*있음|있음|함)\)\s*$")


        

    # ------------------------------------------------------------
    # [메인 함수] PDF 텍스트 → 발언 세그먼트 파싱 파이프라인
    # ------------------------------------------------------------
    # [목적]
    # Extraction 단계가 완료된 PDF 텍스트 데이터를 조회하여,
    # 화자 단위 발언(segment) 구조로 변환하고 DB에 저장한다.
    #
    # [핵심 동작]
    # 1. PARSED 이전 상태의 PDF 텍스트 데이터 조회
    # 2. zlib 압축 해제 및 PageTextSchema 리스트 복원
    # 3. 페이지별 텍스트 라인을 순회하며 화자 발언 감지
    # 4. SegmentSchema 및 PageSegmentsSchema 구조 생성
    # 5. 결과 저장 및 프로세스 상태 PARSED로 업데이트
    # ------------------------------------------------------------
    async def segmentize_pages(self, limit: int = 1):
        
        # -- [Step 1] 대상 조회 (Extraction 완료된 건들) --
        targets = await self.db_repo.get_text_by_status(limit)

        if not targets:
            print("처리할 PDF가 없음")
            return 
        
        processed_count = 0

        for process_row in targets:
            try: 
                process_id = process_row.id

                # [1-1] 압축 데이터 가져오기
                if not process_row.content or not process_row.content.compressed_page_texts:
                    print(f"[Skip] Process ID {process_id}: 텍스트 데이터 없음")
                    # await self.db_repo.update_process_status(process_id, ProcessStatus.FAILED)
                    continue

                # [1-2] 압축 해제 (리스트 Dict 형태)
                pages_data_objects: List[PageTextSchema]= self._get_page_text_object(process_row.content.compressed_page_texts)

                if not pages_data_objects: 
                    print(f"[Skip] Process ID {process_id}: 데이터 포맷 오류 또는 빈 데이터")
                    # await self.db_repo.update_process_status(process_id, ProcessStatus.FAILED)
                    continue

                print(f"[Start] Process ID {process_id} 세그먼테이션 시작 (총 {len(pages_data_objects)}페이지)")

                # -- [Step 2] 문서 파싱 로직(단일 문서 처리) --
                doc_pages = DocumentPageSegmentsSchema(pages=[])
                
                # [상태 유지 변수]
                # 페이지 루프 밖에서 관리해야 페이지가 넘어가도 끊기지 않음
                # 화자(이름 + 역할), 화자의 말
                current_speaker_info = None # (name, role)
                current_text_lines = [] 
                match_count = 0

                # 페이지 반복
                for page_item in pages_data_objects:

                    # Dict -> 객체 or 변수 변환
                    page_number = page_item.page_num
                    text = page_item.text


                    # 현재 페이지의 세그먼트들을 담을 리스트 
                    page_segments: list[SegmentSchema] = []

                    # 페이지내 세그먼트 ID 카운트
                    local_segment_id = 1

                    lines = text.splitlines()
                    for line in lines:
                        line = line.strip()
                        if not line: continue
                        
                        # [2-1]머리말(Header) 제거 로직
                        if self.HEADER_RE.match(line):
                            continue 


                        # [2-2] 종료 패턴 감지 ("산회")
                        if self.STOP_PATTERN.search(line):
                            # 현재까지의 버퍼 저장 후 전체 종료
                            if current_speaker_info and current_text_lines:
                                self._add_segment_info(page_segments, page_number, local_segment_id, current_speaker_info, current_text_lines)
                                current_text_lines = []
                            break 

                        # [2-3] 의사일정 목록 감지
                        # 확실한 안건 목록 패턴 존재 시, 이전 화자의 발언을 저장하고 화자 상태를 해제
                        if self.AGENDA_RE.match(line):
                            if current_speaker_info and current_text_lines:
                                self._add_segment_info(page_segments, page_number, local_segment_id, current_speaker_info, current_text_lines)
                                local_segment_id += 1 
                                current_text_lines = []
                            
                            current_speaker_info = None # 화자 해제: 이제부터 나오는 텍스트는 다음 화자까지 무시
                            continue
                        
                        # [2-4] 집단 응답 감지 시 "완전 무시"
                        if self.COLLECTIVE_RE.match(line):
                            continue
                        
                        # [2-5] 새 화자 패턴 
                        # ◯ 로 시작하는지 확인
                        match = self.SPEAKER_RE.match(line)
                        if match:
                            # 파이썬 로직으로 이름/직책/내용 분리
                            full_line = match.group("Line").strip()
                            name, role, content = self._parse_speaker_line_logic(full_line)

                            # 파싱 실패 시 -> 일반 텍스트로 취급
                            if name == "Unknown":
                                if current_speaker_info:
                                    current_text_lines.append(line)
                                continue 

                            match_count += 1 
                            if match_count <= 3:
                                print(f"MATCH: {name}({role}) -> {content[:20]}...")

                            # 이전에 모아둔 발언이 있다면 저장 (이전 화자의 발언 끝)
                            if current_speaker_info and current_text_lines:
                                self._add_segment_info(page_segments, page_number, local_segment_id, current_speaker_info, current_text_lines)
                                local_segment_id += 1
                                current_text_lines = [] # 버퍼 비우기
                    
                            # 새 화자 정보 업데이트
                            current_speaker_info = (name, role)

                            if content: 
                                current_text_lines.append(content)
                            continue

                        # [2-6] 텍스트 누적 (화자가 식별된 상태일 때만)
                        if current_speaker_info:
                            current_text_lines.append(line)
                
                    # [페이지 끝 처리]
                    # 페이지가 끝났을 때 버퍼에 내용이 있다면 저장해야 한다.
                    # (발언이 다음 페이지로 이어지더라도, 현재 페이지의 텍스트는 여기서 끊어서 저장)
                    if current_speaker_info and current_text_lines: 
                        self._add_segment_info(page_segments, page_number, local_segment_id, current_speaker_info, current_text_lines)

                        # [중요]
                        # 텍스트 버퍼는 비우지만, 화자 정보(current_speaker_info)는 유지
                        # 다음 페이지 첫 줄이 화자 이름 없이 텍스트로 시작하면, 이 화자의 발언으로 간주
                        current_text_lines = []
                
                    # 페이지 결과 추가
                    if page_segments: 
                        doc_pages.pages.append(
                            PageSegmentsSchema(
                                page=page_number,
                                segments=page_segments
                            )
                        )

                    await self.db_repo.save_transcript_parser_result(process_id, doc_pages)
                    await self.db_repo.update_process_status(process_id, ProcessStatus.PARSED)
                    processed_count += 1 
                    print(f"[성공] Process ID {process_id} 파싱 완료 (매칭: {match_count}건)")

            
            except Exception as e:
                print(f"[Error] Process ID {process_row.id} 처리 중 오류: {e}")
                await self.db_repo.update_process_status(process_row.id, ProcessStatus.FAILED)

        # -- [Step 4] 커밋
        if processed_count > 0:
            await self.db_repo.commit()
            print(f"총 {processed_count}건 처리 완료 및 커밋됨.")
        
        return processed_count
    
    # ------------------------------------------------------------
    # [보조 함수] 화자 라인 파싱 로직
    # ------------------------------------------------------------
    # [목적]
    # "소위원장 김용민 의사진행..." 형태의 문자열에서
    # 화자 이름, 직책, 발언 내용을 분리 추출한다.
    #
    # [핵심 동작]
    # - 공백 기준 토큰 분리
    # - "이름 위원", "직책 이름", "부처명 직책 이름" 패턴 분기 처리
    # - 실패 시 안전하게 기본값 반환
    # ------------------------------------------------------------
    def _parse_speaker_line_logic(self, text: str) -> Tuple[str, str, str]:
        """
        문자열을 공백으로 쪼개서 이름/직책/내용을 추론합니다.
        예: "소위원장 김용민 의석을..." -> Name=김용민, Role=소위원장, Content=의석을...
        예: "이강일 위원 의사진행..." -> Name=이강일, Role=위원, Content=의사진행...
        """
        parts = text.split()
        if len(parts) < 2:
            return "Unknown", "Unknown", ""

        # [전략] 앞의 두 단어를 보고 패턴 판단
        token1 = parts[0]
        token2 = parts[1]
        
        # 나머지 텍스트 (내용)
        content_start_idx = 2
        
        # 1. 패턴: "이름 위원" (가장 흔함)
        if token2 in ["위원", "의원"]:
            name = token1
            role = token2
        
        # 2. 패턴: "직책 이름" (소위원장 홍길동, 장관 김철수 등)
        # 이름은 보통 2~4글자이고 조사가 붙지 않음
        elif 2 <= len(token2) <= 4:
            role = token1
            name = token2
        
        # 3. 예외 케이스: "국토교통부 장관 박상우" (직책이 띄어쓰기 된 경우)
        elif len(parts) >= 3 and 2 <= len(parts[2]) <= 4:
            # 세 번째 단어가 이름 같으면? (앞 두 개를 합쳐서 직책으로 봄)
            # 예: 국무 1차장 김영수
            role = f"{token1} {token2}"
            name = parts[2]
            content_start_idx = 3
        else:
            # 판단 불가 (그냥 첫 단어를 직책, 둘째를 이름으로 가정하거나 실패 처리)
            # 여기서는 안전하게 Role=Token1, Name=Token2로 처리
            role = token1
            name = token2

        # 내용 합치기
        content = " ".join(parts[content_start_idx:])
        
        return name, role, content
    
    # ------------------------------------------------------------
    # [보조 함수] 발언 세그먼트 객체 생성 및 리스트 추가
    # ------------------------------------------------------------
    # [목적]
    # 현재까지 누적된 화자 발언 텍스트를 SegmentSchema 객체로
    # 변환하여 페이지 세그먼트 리스트에 추가한다.
    #
    # [핵심 동작]
    # - segment_id = "{page}_{local_id}" 형식으로 생성
    # - speaker_name, speaker_role, text 필드 매핑
    # - segment_list에 append 수행
    # ------------------------------------------------------------
    def _add_segment_info(self, segment_list, page_num, seg_id, speaker_info, text_lines):
        """
        세그먼트 생성 및 리스트 추가 헬퍼
        """
        segment = SegmentSchema(
            segment_id=f"{page_num}_{seg_id}",
            page=page_num,
            speaker_name=speaker_info[0],
            speaker_role=speaker_info[1],
            text="\n".join(text_lines)
        )
        segment_list.append(segment)
    

    # ------------------------------------------------------------
    # [보조 함수] 압축된 페이지 텍스트 복원
    # ------------------------------------------------------------
    # [목적]
    # DB에 zlib 압축 + JSON 직렬화된 페이지 텍스트 데이터를
    # TotalPageTextSchema → PageTextSchema 리스트 형태로 복원한다.
    #
    # [핵심 동작]
    # - zlib.decompress로 바이너리 복원
    # - UTF-8 디코딩 후 JSON 문자열 획득
    # - Pydantic 모델 검증 및 역직렬화 수행
    # - 실패 시 빈 리스트 반환
    # ------------------------------------------------------------
    def _get_page_text_object(self, compressed_data: bytes) -> List[PageTextSchema]:
        """
        1단계에서 TotalPageTextSchema로 저장했으므로
        TotalPageTextSchema로 파싱 후 내부 리스트 반환
        """
        if not compressed_data: 
            return []
        
        try: 
            # 1. 압축 해제
            decompressed_bytes = zlib.decompress(compressed_data)

            # 2. 문자열로 디코딩
            json_str = decompressed_bytes.decode('utf-8')

            # 3. Pydantic 스키마로 검증 및 파싱
            total_data = TotalPageTextSchema.model_validate_json(json_str)

            # 3. JSON 파싱
            return total_data.page_list
        except Exception as e:
            print(f"압축 해제 실패: {e}")
            return []
