import asyncio 
from sqlalchemy import select 
from sqlalchemy.orm import selectinload

from elasticsearch import helpers

from app.dependencies.db import get_db
from app.models import Document, DocumentSegment

from app.search.connection import es_async, es_sync
from app.search.index_manager import INDEX_NAME

"""
제목: 회의록 Elasticsearch 색인기(Indexer)
목적: RDB(DocumentSegment + Document) 데이터를 Elasticsearch 문서로 변환·적재
핵심동작: DB에서 배치 조회 → ES Bulk API로 비동기 색인 수행
"""
class MinutesIndexer: 
    def __init__(self):
        self.index_name = INDEX_NAME
    
    async def index_all_documents(self, batch_size: int=500):
        """
        제목: 전체 문서 세그먼트 색인
        목적: 임베딩이 완료된 모든 세그먼트를 ES인덱스에 일괄 적재
        핵심동작: Paging 조회 -> JSON 변환 -> async_bulk로 배치 색인
        """
        print(f"[Indexer] 전체 데이터 색인 시작 (Batch: {batch_size})")

        async for db in get_db():
            # 임베딩이 완료된(벡터가 있는) 세그먼트만 조회
            # Document 정보도 함께 로딩(Join)
            offset = 0 
            total_indexed = 0 

            while True:
                # ===============================
                # 제목: 1단계 - DB 배치 조회
                # 목적: 메모리 과부하 없이 세그먼트를 페이지 안위로 로딩
                # 핵심동작: embedding_vector가 존재하는 세그먼트만 limit/offset으로 조회
                # ===============================
                stmt = (
                    select(DocumentSegment)
                    .options(selectinload(DocumentSegment.document)) # 부모 정보 로딩
                    .where(DocumentSegment.embedding_vector.isnot(None)) # 벡터 있는 것만
                    .limit(batch_size)
                    .offset(offset)
                )
                result = await db.execute(stmt)
                segments = result.scalars().all()

                if not segments:
                    break 

                # ===============================
                # 제목: 2단계 - RDB -> ES 문서 변환
                # 목적: ORM 객체를 Elasticsearch 인덱싱 포맷(JSON)으로 매핑
                # 핵심동작: Document + Segment 필드 하나를 source 딕셔너리로 구성
                # ===============================
                actions = []
                for seg in segments:
                    doc = seg.document # 부모 문서
                    
                    # className 추가하기 
                    source = {
                        # --- 메타 데이터 ---
                        "doc_id": str(doc.id),
                        "title": doc.title,
                        "committee_name": doc.committeeName,
                        "conf_date": doc.confDate.isoformat() if doc.confDate else None,
                        "confer_num": doc.conferNum,
                        "pdf_link": doc.pdfLinkUrl,
                        
                        # --- 발언 데이터 ---
                        "segment_id": str(seg.id),
                        "page_number": seg.page_number,
                        "speaker_name": seg.speaker_name,
                        "speaker_role": seg.speaker_role,
                        
                        # --- 검색 데이터 ---
                        "content_text": seg.original_text,
                        "keywords": seg.keywords, # List[str]
                        "embedding_vector": seg.embedding_vector # List[float]
                    }

                    # Bulk Action 구조
                    action = {
                        "_index": self.index_name, 
                        "_id": str(seg.id), # 문서 ID는 세그먼트 ID로
                        "_source": source
                    }

                    actions.append(action)

                # ===============================
                # 제목: 3단계 - Elasticsearch Bulk 색인
                # 목적: 네트워크 호출 횟수를 줄이고 대량 데이터를 효율적으로 적재
                # 핵심동작: helpers.async_bulk를 사용해 비동기 일괄 전송
                # ===============================
                if actions:
                    # async_bulk를 사용하여 비동기 전송
                    success_count, errors = await helpers.async_bulk(es_async, actions)
                    total_indexed += success_count 
                    print(f" {success_count}건 색인 완료 (누적: {total_indexed})")

                    if errors:
                        print(f"오류 발생: {errors}")
                
                offset += batch_size 

            print(f"[Indexer] 전체 완료. 총 {total_indexed}건 색인됨.")
            return total_indexed

