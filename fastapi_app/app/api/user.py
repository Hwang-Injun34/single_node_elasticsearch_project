# app/api/v1/indexing.py

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from app.search.indexer import MinutesIndexer # 위에서 정의한 인덱서
import asyncio

router = APIRouter()
indexer = MinutesIndexer()

# 여기는 복사붙여넣기함 제대로 모름

# 인덱싱 상태를 추적하기 위한 단순 플래그 (프로덕션에서는 Redis/DB 사용 권장)
is_indexing_running = False

async def run_indexing_and_cleanup():
    global is_indexing_running
    is_indexing_running = True
    try:
        # 실제 색인 작업 실행
        result = await indexer.index_all_documents(batch_size=500)
        print(f"Indexing job finished successfully: {result}")
    except Exception as e:
        print(f"Indexing job failed: {e}")
    finally:
        is_indexing_running = False

@router.post("/start_indexing", status_code=status.HTTP_202_ACCEPTED)
async def start_indexing(background_tasks: BackgroundTasks):
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
    background_tasks.add_task(run_indexing_and_cleanup)
    
    return {"message": "Indexing started in the background.", "status": "processing"}

@router.get("/indexing_status")
async def get_status():
    """색인 작업의 현재 상태를 확인합니다."""
    return {"running": is_indexing_running}

# 그리고 main.py에서 이 라우터를 포함시켜야 합니다.