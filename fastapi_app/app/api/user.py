from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from app.search.indexer import MinutesIndexer
import asyncio
import time  # ✅ 시간 측정을 위해 추가

router = APIRouter()
indexer = MinutesIndexer()

# 인덱싱 상태 추적 플래그
is_indexing_running = False

async def run_indexing_and_cleanup(batch_size: int):
    global is_indexing_running
    is_indexing_running = True
    
    # ✅ [1] 시작 시간 기록
    start_time = time.time()
    print(f"\n🚀 [Start] 색인 작업을 시작합니다. (Batch Size: {batch_size})")

    try:
        # 실제 색인 작업 실행
        # indexer가 처리한 문서 수(int)를 반환한다고 가정
        result = await indexer.index_all_documents(batch_size=batch_size)
        
        # result가 숫자가 아닐 경우를 대비한 안전장치
        count = result if isinstance(result, int) else 0
        
        # ✅ [2] 종료 시간 기록 및 계산
        end_time = time.time()
        duration = end_time - start_time
        throughput = count / duration if duration > 0 else 0
        
        # ✅ [3] 결과 로그 출력 (터미널에서 바로 확인 가능)
        print(f"---------------------------------------------")
        print(f"✅ [Complete] 색인 작업 완료")
        print(f" - 총 문서 수 : {count} 건")
        print(f" - 소요 시간  : {duration:.2f} 초")
        print(f" - 처리량     : {throughput:.2f} docs/sec")
        print(f"---------------------------------------------\n")

    except Exception as e:
        print(f"❌ [Error] 색인 작업 실패: {e}")
    finally:
        is_indexing_running = False

@router.post("/start_indexing", status_code=status.HTTP_202_ACCEPTED)
async def start_indexing(background_tasks: BackgroundTasks, batch_size: int = 500):
    """
    전체 문서를 Elasticsearch에 색인하는 작업을 백그라운드에서 시작합니다.
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
    """색인 작업의 현재 상태를 확인합니다."""
    return {"running": is_indexing_running}