import time 
import asyncio
from typing import List
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.repositories.pdf_process.p03_track_b import PdfEmbeddingExtractorRepository
# ============================================================
# Track B - PDF 발언 세그먼트 임베딩 벡터 생성 서비스
# ------------------------------------------------------------
# [제목]
# PdfEmbeddingExtractorService
#
# [목적]
# 키워드 추출이 완료된 발언 세그먼트 텍스트를
# SentenceTransformer 모델을 이용해 벡터 임베딩으로 변환하여
# 검색, 추천, 유사도 계산 등에 활용할 수 있도록 저장한다.
#
# [핵심 동작]
# - 임베딩이 없는 세그먼트 조회
# - CPU-bound 임베딩 연산을 asyncio.to_thread로 비동기 처리
# - 세그먼트 ID ↔ 임베딩 벡터 매핑 후 DB에 일괄 저장
# ============================================================

# ============================================================
# PdfEmbeddingExtractorService
# ------------------------------------------------------------
# [제목]
# 발언 세그먼트 임베딩 생성 서비스 클래스
#
# [목적]
# DocumentSegment.original_text 필드를 기반으로
# 고차원 의미 벡터를 생성하고 DB에 저장한다.
#
# [핵심 동작]
# - SentenceTransformer 모델 래핑
# - 세그먼트 리스트 단위 배치 임베딩 처리
# - 벡터 결과를 DB 저장 구조로 변환
# ============================================================
class PdfEmbeddingExtractorService:
    def __init__(self, db_p03_track_b: PdfEmbeddingExtractorRepository, model_instance: SentenceTransformer):
        """
        model_name: 사용할 SentenceTransformer 모델 이름
        """
        self.db_repo = db_p03_track_b
        self.model = model_instance

    # ------------------------------------------------------------
    # [메인 함수] 발언 세그먼트 임베딩 생성 파이프라인
    # ------------------------------------------------------------
    # [목적]
    # 임베딩 벡터가 아직 생성되지 않은 세그먼트를 조회하여
    # SentenceTransformer 모델을 통해 벡터화하고 DB에 저장한다.
    #
    # [핵심 동작]
    # 1. 임베딩 대상 세그먼트 조회
    # 2. asyncio.to_thread로 CPU-bound 임베딩 작업 분리 실행
    # 3. 세그먼트 ID ↔ 벡터 결과 매핑
    # 4. DB 일괄 업데이트 및 커밋
    # ------------------------------------------------------------
    async def run_embedding_extraction(self):
        """
        벡터가 없는 세그먼트 조회 -> 임베딩 -> 저장
        """
        # -- [Step 1] 대상 조회
        target_processes = await self.db_repo.get_segments_by_status()

        if not target_processes:
            print("[Track B] 처리할 세그먼트가 없습니다.")
            return
        
        print(f"---------- [Track B] {len(target_processes)}개 세그먼트 임베딩 시작 ----------")

        total_segments_count = 0

        for process in target_processes:

            try: 
                segments = process.segment
                if not segments:
                    print(f"[Skip] Process ID {process.id}: 세그먼트 없음")
                    continue
                
                print(f"[Start] Process ID {process.id} (세그먼트 {len(segments)}개)")

                # -- [Step 2] 비동기 임베딩 실행(CPU Bound) --
                # to_thread로 CPU 작업 분리
                processed_data = await asyncio.to_thread(self._process_segments_embedding, segments)

                # -- [Step 3] DB 업데이트 --
                await self.db_repo.update_vectors_bulk(processed_data)
                print(f"총 {len(processed_data)}건 임베딩 및 저장 완료")

                total_segments_count += len(segments)
                print(f"[성공]] Process ID {process.id} 완료")
            except Exception as e:
                print(f"[Error] Process ID {process.id} 처리 실패: {e}")
                # await self.db_repo.update_process_status(process.id, ProcessStatus.FAILED)
        await self.db_repo.commit()

    # ------------------------------------------------------------
    # [보조 함수] 세그먼트 배치 임베딩 처리기
    # ------------------------------------------------------------
    # [목적]
    # 세그먼트 객체 리스트를 입력받아
    # SentenceTransformer 모델을 통해 벡터 임베딩을 생성한다.
    #
    # [핵심 동작]
    # - original_text 필드 추출
    # - 모델 배치 인코딩 실행
    # - {id, embedding_vector} 구조로 결과 매핑
    # ------------------------------------------------------------
    def _process_segments_embedding(self, segments: List) -> List:
        # 1. 텍스트 추출
        texts = [seg.original_text for seg in segments]

        # 2. 모델 인코딩(배치 처리)
        vectors = self.model.encode(texts, show_progress_bar=True)

        # 3. 결과 매핑(ID + Vector)
        result_list = []
        for i, seg in enumerate(segments):
            vector_list = vectors[i].tolist()

            result_list.append({
                "id": seg.id, 
                "embedding_vector": vector_list
            })

        return result_list
