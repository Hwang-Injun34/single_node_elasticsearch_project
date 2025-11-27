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
    # 메인 크롤링 실행 (위원회 회의록 - JSON API 방식)
    # ----------------------------------------
    async def na_crawl(self, filters: CrawlerFilter):
        # 1. URL 설정 (www.assembly.go.kr 기준)
        base_domain = settings.NA_BASE_URL # https://www.assembly.go.kr
        
        # CSRF 토큰을 얻기 위한 메인 화면
        main_url = f"{base_domain}/portal/main/contents.do?menuNo=600045"
        
        # 실제 데이터를 요청할 API 주소
        api_url = f"{base_domain}/portal/cnts/cntsCmmit/listMtgRcord.json"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Referer": main_url,
            "Origin": base_domain
        }

        all_data = []
        current_page = 1
        total_collected_count = 0 

        # 날짜 필터 포맷팅 (YYYYMMDD)
        sdate_str = filters.start_date.strftime("%Y%m%d") if filters.start_date else ""
        edate_str = filters.end_date.strftime("%Y%m%d") if filters.end_date else ""

        print(f"🚀 크롤링 시작 | Limit: {filters.limit} | 기간: {sdate_str}~{edate_str}")

        async with httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True) as client:
            
            # =========================================================
            # [Step 1] 메인 페이지 접속하여 CSRF 토큰 획득 (필수 ⭐)
            # =========================================================
            print("🚪 메인 페이지 접속 및 보안 토큰 확보 중...")
            try:
                main_res = await client.get(main_url)
                soup = BeautifulSoup(main_res.text, "html.parser")
                
                # <meta name="_csrf" content="..."> 태그 찾기
                csrf_meta = soup.select_one("meta[name='_csrf']")
                
                if not csrf_meta:
                    print("❌ CSRF 토큰을 찾을 수 없습니다. (사이트 구조 변경됨)")
                    return []
                
                csrf_token = csrf_meta['content']
                # print(f"   🔑 Token 확보 완료: {csrf_token[:10]}...")

            except Exception as e:
                print(f"❌ 초기 접속 실패: {e}")
                return []

            # =========================================================
            # [Step 2] 데이터 요청 루프 (Pagination)
            # =========================================================
            while True:
                # 목표 수량 도달 체크 (-1은 무제한)
                if filters.limit != -1 and total_collected_count >= filters.limit:
                    print(f"🛑 목표 수량({filters.limit}개) 달성으로 종료.")
                    break

                print(f"\n📄 [Page {current_page}] API 요청 중...")

                # POST 데이터 구성 (Form Data)
                payload = {
                    "menuNo": "600045",          # 메뉴번호 (고정)
                    "pageIndex": str(current_page),
                    "cntsDivCd": "CMMIT",        # 콘텐츠 구분 (위원회)
                    "committeeCd": "",           # 전체 위원회
                    "title": "",                 # 검색어
                    "beginDate": sdate_str,      # 시작일
                    "endDate": edate_str,        # 종료일
                    "_csrf": csrf_token          # ⭐ 토큰 필수
                }

                try:
                    # API 호출 (POST)
                    res = await client.post(api_url, data=payload)
                    data = res.json()
                    
                    # 결과 리스트 추출
                    result_list = data.get("resultList", [])
                    
                    # 종료 조건: 데이터가 없으면 끝
                    if not result_list:
                        print("✅ 더 이상 데이터가 없습니다.")
                        break
                    
                    print(f"   🔍 {len(result_list)}개의 문서 발견")

                    # --- 리스트 반복 처리 ---
                    for item in result_list:
                        # 목표 수량 체크
                        if filters.limit != -1 and total_collected_count >= filters.limit: break

                        try:
                            # 1. JSON 데이터 파싱
                            # item 예시: {'committeeName': '법제사법위', 'title': '...', 'pdfLinkUrl': '...', ...}
                            
                            title = item.get("title", "").strip()
                            committee_name = item.get("committeeName", "").strip()
                            conf_date_str = item.get("confDate", "").strip() # YYYY.MM.DD
                            pdf_link = item.get("pdfLinkUrl") # PDF 링크 (없을 수 있음)

                            # PDF 없는 회의록은 스킵
                            if not pdf_link:
                                # print(f"   ⏭️ [Skip] PDF 없음: {title}")
                                continue

                            # 2. 파일 ID 추출
                            # 링크 예시: /portal/comm/download/downloadFile.do?fileId=2023...
                            file_id = None
                            if "fileId=" in pdf_link:
                                file_id = pdf_link.split("fileId=")[1].split("&")[0]
                            
                            # ID가 없으면 제목+날짜로 고유 ID 생성 (중복 체크용)
                            if not file_id:
                                safe_temp_title = re.sub(r'\s+', '', title)
                                file_id = f"{conf_date_str}_{safe_temp_title}"

                            # 3. 중복 체크 (DB)
                            if await self.db_repo.is_crawled(doc_id=file_id):
                                print(f"   ⏭️ [Skip] 이미 수집됨: {title}")
                                continue

                            print(f"   ▶️ 수집 시작: {title}")

                            # 4. 다운로드 URL 완성
                            if not pdf_link.startswith("http"):
                                download_url = base_domain + pdf_link
                            else:
                                download_url = pdf_link

                            # 5. 파일명 생성 및 경로 설정
                            safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
                            filename = f"{conf_date_str}_{file_id}_{safe_title}.pdf"
                            file_path = os.path.join(settings.PDF_DIR, filename)

                            # 6. 파일 다운로드
                            file_res = await client.get(download_url)
                            if file_res.status_code == 200:
                                with open(file_path, "wb") as f:
                                    f.write(file_res.content)
                                

                                # 8. DB 저장 (Schema -> DB Model)
                                doc_data = DocumentCreate(
                                    doc_id=file_id,
                                    title=safe_title,
                                    committee_name=committee_name,
                                    meeting_date=meeting_date,
                                    file_url=download_url,
                                    file_path=file_path,
                                    # 위원회 회의록엔 대/회기/차 정보가 JSON에 없을 수 있음 (빈값 처리)
                                    dae_num="",
                                    session_num="",
                                    degree_num=""
                                )

                                # model_dump()로 딕셔너리 변환 후 전달
                                await self.db_repo.save_document(doc_data.model_dump())
                                
                                all_data.append({"id": file_id, "status": "success"})
                                total_collected_count += 1
                                
                                # 서버 부하 방지
                                await asyncio.sleep(random.uniform(0.5, 1.2))
                            else:
                                print(f"      ❌ 다운로드 실패 ({file_res.status_code})")

                        except Exception as e:
                            print(f"      ⚠️ 항목 처리 중 에러: {e}")
                            continue
                    
                    # --- 페이지 증가 ---
                    current_page += 1
                    await asyncio.sleep(1) # 페이지 넘김 대기

                except Exception as e:
                    print(f"   ⚠️ 페이지 요청 실패: {e}")
                    break

        print(f"🏁 크롤링 종료! 총 {total_collected_count}개 수집 완료.")
        return all_data