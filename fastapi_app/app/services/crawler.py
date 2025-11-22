import os
import re
import random
import asyncio
import httpx
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


from app.repositories.crawler import NationalAssemblyCrawlerRepository
from app.core.config import settings
from app.schema.crawler import DocumentCreate, CrawlerFilter

# PDF 저장 경로 생성
os.makedirs(settings.PDF_DIR, exist_ok=True)

class NationalAssemblyCrawlerService:
    def __init__(self, repo: NationalAssemblyCrawlerRepository):
        self.db_repo = repo
    # ----------------------------------------
    # 메인 크롤링 실행
    # ----------------------------------------
    async def na_crawl(self, filters: CrawlerFilter):
        base_url = settings.NA_BASE_URL 
        list_url = base_url + settings.NA_LIST_URL 
        main_url = base_url + settings.NA_MAIN_URL
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Referer": main_url
        }

        all_data = []
        current_page=1 
        total_collected_count = 0 # 현재까지 수집한 총 개수

        # 날짜 포맷 변환(date -> "YYY.MM.DD")
        sdate_str = filters.start_date.strftime("%Y.%m.%d") if filters.start_date else ""
        edate_str = filters.end_date.strftime("%Y.%m.%d") if filters.end_date else ""

        print(f"크롤링 시작 | 제한: {filters.limit}개 | 대수: {filters.parliament_num or '전체'} | 기간: {sdate_str}~{edate_str}")

        async with httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True) as client:
            
            # [Step 1] 메인 페이지 접속하여 세션 획득
            print("국회 사이트 접속 중..(세션 획득)")
            await client.get(main_url)

            # --------------------------
            # [Loop] 페이지 반복 시작
            # -------------------------- 
            while True: 

                # 목표 수량 도달 시 종료 로직
                # limit이 -1 이면 무제한 (카운트 체크 안 함)
                # limit이 양수이면 카운트 체크
                if filters.limit != -1 and total_collected_count >= filters.limit:
                    print(f"목표 수량({filters.limit}개) 도달로 종료")
                    break

                print(f"[페이지 {current_page}] 수집 시작")

                # 쿼리 파라미터 설정(URL 뒤에 붙는 것들)
                # https://record.assembly.go.kr/assembly/mnts/apdix/list.do?schwrd=&sel_date=&sdate=&flag=all&sel_group=&limit=&page=6&sel_align=&edate=&list_style=&schword=
                params = {
                    "page": current_page,
                    "limit": 10, 
                    "sdate": sdate_str,
                    "edate": edate_str,
                    "flag": "all",
                    "schwrd":"","sel_date":"",
                    "sel_group": "", "sel_align": "",
                    "list_style": "", "schword": ""
                }

                # [Step 2] 목록 페이지 요청(params 포함)
                res = await client.get(list_url, params=params)

                # [Step 3] 파싱 시작
                soup = BeautifulSoup(res.text, "html.parser")
                tbody = soup.select_one("#listData")
                
                # 종료 조건 1: 목록 태그가 아예 없을 때
                if not tbody:
                    print("데이터 목록(tbody)을 찾을 수 없음")
                    break
            
                rows = tbody.select("tr")

                # 종료 조건 2: 행이 하나도 없거나, '데이터가 없습니다' 문구가 있을 때
                if not rows or (len(rows) == 1 and "데이터가" in row[0].text):
                    print("더 이상 데이터가 없습니다. (마지막 페이지)")
                    break 

                print(f"{len(rows)}개의 문서 발견 (현재 페이지)")

                # --- 페이지 내 행 반복 ---
                for row in rows: 
                    # 목표 수량 채우면 즉시 종료
                    if filters.limit != -1 and total_collected_count >= filters.limit: break

                    cols = row.select("td")
                    if len(cols) < 6: continue

                    try: 
                        # --- 1. 기본 정보 추출 ---
                        parliament = cols[1].text.strip()
                        meeting_series = cols[2].text.strip()
                        meeting_number = cols[3].text.strip()
                        date_str = cols[5].text.strip()

                        # ----- [파이썬 필터링] 서버가 모소 거른 조건 체크

                        # (1) 대수 필터(에: '22'입력 시 '제22대' 포함 여부 확인
                        if filters.parliament_num:
                            if filters.parliament_num not in parliament:
                                continue 

                        # (2) 날짜 2차 검증
                        # date_str -> date 객체 변환
                        try:
                            row_date = datetime.strptime(date_str.rstrip('.'), "%Y.%m.%d").date()
                            
                            if filters.start_date and row_date < filters.start_date: continue
                            if filters.end_date and row_date > filters.end_date: continue
                        except:
                            pass # 날짜 파싱 에러나면 일단 진행 (or 스킵)


                        # --- 2. 제목 및 링크 추출 ---
                        subject_td = cols[4]
                        a_tag = subject_td.select_one("a")

                        if not a_tag: continue 

                        title = a_tag.text.strip() # 제목
                        href = a_tag.get('href') # 파일

                        # href가 상대경로면 전체 URL 생성
                        full_href = base_url + href 
                        parsed = urlparse(full_href)
                        qs = parse_qs(parsed.query)
                    
                        # --- 3. ID 추출 --- 
                        # 중복 방지
                        file_id = qs.get('fileId', [None])[0]

                        if not file_id:
                            print(f"파일 ID 추출 실패 {href}")
                            continue 

                        # --- 4. 중복 체크 ---
                        if await self.db_repo.is_crawled(file_id=file_id):
                            print(f"[Skip] 이미 수집됨: {title} ({file_id})")
                            continue

                        print(f"수집 시작: {title}")


                        # --- 5. 파일명 생성(특수문자 제거) ---
                        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
                        filename = f"{date_str.rstrip('.')}_{file_id}_{safe_title}.pdf"
                        file_path = os.path.join(settings.PDF_DIR, filename)

                        # --- 6. 다운로드 실행 ---
                        print(f"다운로드...{full_href}")
                        file_res = await client.get(full_href)

                        if file_res.status_code == 200:
                            with open(file_path, "wb") as f:
                                f.write(file_res.content)

                            # --- 7. 날짜 변환 (2024.11.04 -> date 객체)
                            try:
                                meeting_date = datetime.strptime(date_str.rstrip('.'), "%Y.%m.%d").date()   
                            except:
                                meeting_date = None
                        
                            # --- 8. DB 저장 ---
                            doc_data = DocumentCreate(
                                parliament=parliament,
                                meeting_series=meeting_series,
                                meeting_number=meeting_number,
                                title=safe_title,
                                file_id=file_id,
                                file_url=full_href,
                                file_path=file_path,
                                meeting_date=meeting_date
                            )

                            await self.db_repo.save_document(doc_data.model_dump()) 
                            print("저장 완료")

                            all_data.append({"id": file_id, "status": "success"})
                            total_collected_count += 1

                            # 서버 부하 방지
                            await asyncio.sleep(random.uniform(0.5, 1.5))
                
                        else:
                            print(f"다운로드 실패: {file_res.status_code}")
                    except Exception as e:
                        print(f"처리 중 에러: {e}")
                        continue
                
                # 페이지 내 루프 끝
                # 다음 페이지로 이동
                current_page += 1 

                # 페이지 넘길 때도 딜레이 필요
                await asyncio.sleep(1)
        print(f"크롤링 종료. 총{total_collected_count}개 수집 완료.")
        return all_data

