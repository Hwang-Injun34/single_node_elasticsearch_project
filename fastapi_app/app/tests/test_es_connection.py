import pytest
from app.search.connection import check_es_connection, es_async

@pytest.mark.asyncio
async def test_elasticsearch_ping():
    """
    Elasticsearch 연결 테스트
    """
    print("\n🚀 [Test] Elasticsearch 연결 테스트 시작...")
    
    # 1. 실제 연결 테스트 함수 호출
    await check_es_connection()
    
    # 2. 직접 ping 날려보기 (검증)
    is_connected = await es_async.ping()
    
    if is_connected:
        print("✅ [Test] 연결 성공! (True 반환)")
    else:
        print("❌ [Test] 연결 실패! (False 반환)")
        # 실패 시 클러스터 정보 조회 시도 (에러 메시지 확인용)
        try:
            info = await es_async.info()
            print(f"ℹ️ Cluster Info: {info}")
        except Exception as e:
            print(f"❌ 접속 에러 상세: {e}")

    # 3. Assert (테스트 통과/실패 결정)
    assert is_connected == True, "Elasticsearch에 연결할 수 없습니다."