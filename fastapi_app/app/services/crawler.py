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

    # ===============================
    # 메인 크롤링 실행 (위원회 회의록 - JSON API 방식)
    # ===============================
    async def na_crawl(self, filters: CrawlerFilter):
        base_url = settings.NA_BASE_URL 

        # CSRF 토큰을 얻기 위한 메인 화면
        main_url = base_url + settings.NA_MAIN_URL

        # 실제 데이터 요청할 API 주소
        api_url = base_url + settings.NA_API_URL
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Referer": main_url,
            "Origin": base_url
        }

        all_data = []
        current_page=1 
        total_collected_count = 0 # 현재까지 수집한 총 개수

        # 날짜 포맷 변환(date -> "YYY.MM.DD")
        sdate_str = filters.beginDate.strftime("%Y%m%d") if filters.beginDate else ""
        edate_str = filters.endDate.strftime("%Y%m%d") if filters.endDate else ""
        print(f"크롤링 시작 | Limit: {filters.limit} | 기간: {sdate_str}~{edate_str}")

        async with httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True) as client:

            # --------------------------
            # [Step 1] 메인 페이지 접속하여 CSRF 토큰 획득
            # -------------------------- 
            print("[메인 페이지] 접속 및 보안 토큰 확보 중...")
            try:
                main_res = await client.get(main_url)
                soup = BeautifulSoup(main_res.text, "html.parser")

                # <meta name="_csrf" content="..."> 태그 찾기
                csrf_meta = soup.select_one("meta[name='_csrf']")

                if not csrf_meta:
                    print("CSRF 토큰 찾기 [실패] - 사이트 구조 변경")
                    return []
                csrf_token = csrf_meta['content']

            except Exception as e:
                print(f"초기 접속 [실패]: {e}")
                return []
            
            # --------------------------
            # [Step 2] 데이터 요청 루프 (Pagination)
            # -------------------------- 
            while True:
                # 목표 수량 도달 체크 (-1: 무제한)
                if filters.limit != -1 and total_collected_count >= filters.limit:
                    print(f"목표 수량({filters.limit}개) 달성으로 [종료]")
                    break

                print(f"\n[Page {current_page}] API 요청 중...")

                # POST 데이터 구성(Form Data)
                # menuNo=600045&pageIndex=2&cntsDivCd=CMMIT&committeeCd=&title=&beginDate=&endDate=&_csrf=dce41426-91b1-4c2a-aa68-772fa13222cc
                payload = {
                    "menuNo": "600045",          # 메뉴번호 (고정)
                    "pageIndex": str(current_page),
                    "cntsDivCd": "CMMIT",        # 콘텐츠 구분 (위원회)
                    "committeeCd": "",           # 전체 위원회
                    "title": "",                 # 검색어
                    "beginDate": sdate_str,      # 시작일
                    "endDate": edate_str,        # 종료일
                    "_csrf": csrf_token          # 토큰 필수
                }

                try: 
                    # API 호출 (POST)
                    res = await client.post(api_url, data=payload)
                    data = res.json()

                    # 결과 리스트 호출
                    result_list = data.get("resultList", [])

                    # 종료 조건: 데이터가 없으면 끝
                    if not result_list:
                        print("더 이상 데이터가 없음")
                        break

                    print(f"{len(result_list)}개의 문서 발견")

                    # --- 리스트 반복 처리 ---
                    for item in result_list:
                        # 목표 수량 체크
                        if filters.limit != -1 and total_collected_count >= filters.limit: break 

                        try:
                            """
                            "rn": 1,
                            "conferNum": 55815,
                            "classCode": 2,
                            "className": "상임위원회",
                            "committeeId": "9700409",
                            "committeeName": "외교통일위원회",
                            "title": "제22대 제429회 6차 외교통일위원회 ",
                            "vodLinkUrl": null,
                            "confLinkUrl": "https://record.assembly.go.kr/assembly/viewer/minutes/xml.do?id=55815&type=summary",
                            "hwpLinkUrl": "https://record.assembly.go.kr/assembly/viewer/minutes/download/hwp.do?id=55815",
                            "pdfLinkUrl": "https://record.assembly.go.kr/assembly/viewer/minutes/download/pdf.do?id=55815",
                            "confViewerUrl": "https://record.assembly.go.kr/assembly/viewer/minutes/xml.do?id=55815&type=view",
                            "confDate": "2025-11-19"
                            """
                            # ---- 1. JSON 데이터 파싱 ----
                            className = item.get("committeeName", "").strip()
                            committeeName = item.get("committeeName", "").strip()
                            confDate = item.get("confDate", "").strip()
                            conferNum = str(item.get("conferNum"))
                            pdfLinkUrl = item.get("pdfLinkUrl")
                            title = item.get("title", "").strip()
                            
                            if not pdfLinkUrl:
                                continue 

                            # ---- 2. 중복 체크 (DB) ----
                            if await self.db_repo.is_crawled(conferNum=conferNum):
                                print(f"[Skip] 이미 수집: {title}")
                                continue 

                            print(f"수집 [시작]: {title}")

                            # ---- 3. 날짜 객체 변환 ----
                            try:
                                # 하이픈(-) 포맷에 맞춰 파싱
                                parsed_conf_date = datetime.strptime(confDate, "%Y-%m-%d").date()
                            except Exception:
                                # 날짜가 없거나 형식이 다르면 None 처리
                                parsed_conf_date = None

                            # ---- 4. 파일명 생성 및 경로 설정 ----
                            safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
                            filename = f"{parsed_conf_date}_{conferNum}_{safe_title}.pdf"
                            file_path = os.path.join(settings.PDF_DIR, filename)

                            # ---- 5. 파일 다운로드 ----
                            file_res = await client.get(pdfLinkUrl)
                            if file_res.status_code == 200:
                                with open(file_path, "wb") as f:
                                    f.write(file_res.content)

                                # ---- 6. DB 저장 -----
                                doc_data = DocumentCreate(
                                    className=className,
                                    committeeName=committeeName,
                                    confDate=parsed_conf_date,
                                    conferNum=conferNum,
                                    pdfLinkUrl=pdfLinkUrl,
                                    file_path=file_path,
                                    title=safe_title
                                )

                                await self.db_repo.save_document(doc_data.model_dump())
                                    
                                all_data.append({"id":conferNum, "status":"success"})
                                total_collected_count += 1 

                                await asyncio.sleep(random.uniform(0.5, 1.2))
                            else:
                                print(f"다운로드 [실패] ({file_res.status_code})")


                        except Exception as e:
                            print(f"항목 처리 중 [에러]: {e}")
                            continue
                    
                    # --- 페이지 증가 ---
                    current_page += 1 
                    await asyncio.sleep(1) # 페이지 넘김 대기

                except Exception as e:
                    print(f"페이지 요청 [실패]: {e}")
                    break 

        print(f"크롤링 [종료] | 총 {total_collected_count}개 수집 완료")
        return all_data


