# ... imports 생략 ...
from app.schema.crawler import DocumentCreate, CrawlerFilter # Filter 임포트 추가

class NationalAssemblyCrawlerService:
    # ... init 생략 ...

    # ----------------------------------------
    # 메인 크롤링 실행 (필터 적용 버전)
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
        current_page = 1
        total_collected_count = 0 
        
        # 날짜 포맷 변환 (date -> "YYYY.MM.DD")
        sdate_str = filters.start_date.strftime("%Y.%m.%d") if filters.start_date else ""
        edate_str = filters.end_date.strftime("%Y.%m.%d") if filters.end_date else ""

        print(f"🚀 크롤링 시작 | 제한: {filters.limit}개 | 대수: {filters.parliament_num or '전체'} | 기간: {sdate_str}~{edate_str}")

        async with httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True) as client:
            # [Step 1] 세션 획득
            await client.get(main_url)

            while True:
                # 목표 수량 도달 시 종료
                if total_collected_count >= filters.limit:
                    print(f"🛑 목표 수량({filters.limit}개) 달성.")
                    break

                print(f"\n📄 [Page {current_page}] 요청 중...")

                # [Step 2] 파라미터 구성 (서버 필터링)
                params = {
                    "page": current_page,
                    "limit": 10,
                    "sdate": sdate_str,  # 시작일 (서버 필터)
                    "edate": edate_str,  # 종료일 (서버 필터)
                    "flag": "all",       # 전체 검색
                    # "schword": "검색어" # 필요시 검색어도 추가 가능
                }

                res = await client.get(list_url, params=params)
                soup = BeautifulSoup(res.text, "html.parser")
                tbody = soup.select_one("#listData")

                if not tbody: break
                rows = tbody.select("tr")
                
                # 데이터 없음 체크 (국회 사이트 특성상 문구가 뜰 수 있음)
                if not rows or (len(rows) == 1 and "데이터가" in rows[0].text):
                    print("✅ 더 이상 데이터가 없습니다.")
                    break

                # --- 행 반복 ---
                for row in rows:
                    if total_collected_count >= filters.limit: break

                    cols = row.select("td")
                    if len(cols) < 6: continue

                    try:
                        # 1. 정보 파싱
                        parliament_text = cols[1].text.strip() # 예: 제22대국회
                        date_str = cols[5].text.strip()        # 예: 2024.11.04.
                        
                        # =================================================
                        # 🛡️ [파이썬 필터링] 서버가 못 거른 조건 체크
                        # =================================================
                        
                        # (1) 대수 필터 (예: '22' 입력 시 '제22대' 포함 여부 확인)
                        if filters.parliament_num:
                            # "22" 가 "제22대국회" 안에 없으면 스킵
                            if filters.parliament_num not in parliament_text:
                                # print(f"   ⏭️ [Skip] 대수 불일치: {parliament_text}")
                                continue

                        # (2) 날짜 2차 검증 (혹시 모르니 파이썬에서 확실하게)
                        # date_str -> date 객체 변환
                        try:
                            row_date = datetime.strptime(date_str.rstrip('.'), "%Y.%m.%d").date()
                            
                            if filters.start_date and row_date < filters.start_date: continue
                            if filters.end_date and row_date > filters.end_date: continue
                        except:
                            pass # 날짜 파싱 에러나면 일단 진행 (or 스킵)

                        # -------------------------------------------------
                        # 이 아래는 기존 로직과 동일
                        # -------------------------------------------------
                        subject_td = cols[4]
                        a_tag = subject_td.select_one("a")
                        if not a_tag: continue 

                        title = a_tag.text.strip()
                        href = a_tag.get('href')
                        
                        # ... (ID 추출, 다운로드, DB 저장 로직은 기존 코드 그대로 복붙) ...
                        # ... 중략 ...
                        # file_id 추출 ...
                        # is_crawled 체크 ...
                        # 다운로드 ...
                        # save_document ...
                        
                        # 성공 시 카운트 증가
                        # total_collected_count += 1

                    except Exception as e:
                        print(f"   ⚠️ 에러: {e}")
                        continue
                
                # 페이지 증가
                current_page += 1
                await asyncio.sleep(1)

        return all_data