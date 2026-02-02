from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from app.search.indexer import MinutesIndexer
import time

router = APIRouter()
indexer = MinutesIndexer()

"""
제목: 색인 실행 상태 플래그
목적: 중복 인덱싱 작업 방지
핵심동작: 실행 중 True, 완료 시 False
"""
is_indexing_running = False


"""
제목: 백그라운드 색인 실행 함수
목적: 전체 문서를 Elasticsearch에 비동기 색인
핵심동작: 배치 단위 처리 후 결과 로그 출력
"""
async def run_indexing_and_cleanup(batch_size: int):
    global is_indexing_running
    is_indexing_running = True
    

    start_time = time.time()
    print(f"\n[Start] 색인 작업을 시작합니다. (Batch Size: {batch_size})")

    try:
        # 실제 색인 작업 실행
        # indexer가 처리한 문서 수(int)를 반환한다고 가정
        result = await indexer.index_all_documents(batch_size=batch_size)
        
        # result가 숫자가 아닐 경우를 대비한 안전장치
        count = result if isinstance(result, int) else 0
        
        # 종료 시간 기록 및 계산
        end_time = time.time()
        duration = end_time - start_time
        throughput = count / duration if duration > 0 else 0
        
        # 결과
        print(f"---------------------------------------------")
        print(f"[Complete] 색인 작업 완료")
        print(f" - 총 문서 수 : {count} 건")
        print(f" - 소요 시간  : {duration:.2f} 초")
        print(f" - 처리량     : {throughput:.2f} docs/sec")
        print(f"---------------------------------------------\n")

    except Exception as e:
        print(f"[Error] 색인 작업 실패: {e}")
    finally:
        is_indexing_running = False



@router.post("/start_indexing", status_code=status.HTTP_202_ACCEPTED)
async def start_indexing(background_tasks: BackgroundTasks, batch_size: int = 500):
    """
    제목: 색인 작업 시작 API
    목적: 전체 문서 색인을 백그라운드로 실행
    핵심동작: 실행 중 여부 확인 후 태스크 등록
    """
    global is_indexing_running
    
    if is_indexing_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Indexing job is already running."
        )

    # run_indexing_and_cleanup 함수를 백그라운드에서 실행하도록 등록
    background_tasks.add_task(run_indexing_and_cleanup, batch_size)
    
    return {
        "message": "Indexing started in the background. Check server logs for results.",
        "status": "processing"
    }


@router.get("/indexing_status")
async def get_status():
    """
    제목: 색인 상태 조회 API
    목적: 현재 인덱싱 실행 여부 확인
    핵심동작: 상태 플래그 반환
    """
    return {"running": is_indexing_running}