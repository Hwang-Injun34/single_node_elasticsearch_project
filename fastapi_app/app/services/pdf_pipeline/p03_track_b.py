import time 
import asyncio
from typing import List
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.repositories.pdf_process.p03_track_b import PdfEmbeddingExtractorRepository


# ===============================
# 3단계_TrackB: 임베딩 벡터 생성
# ===============================
class PdfEmbeddingExtractorService:
    def __init__(self, db_p03_track_b: PdfEmbeddingExtractorRepository, model_instance: SentenceTransformer):
        """
        model_name: 사용할 SentenceTransformer 모델 이름
        """
        self.db_repo = db_p03_track_b
        self.model = model_instance

    # -------------------------
    #       [메인 함수]
    # -------------------------
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
                    print(f"⚠️ [Skip] Process ID {process.id}: 세그먼트 없음")
                    continue
                
                print(f"▶️ [Start] Process ID {process.id} (세그먼트 {len(segments)}개)")

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

    # -------------------------
    #       [보조 함수]
    # -------------------------
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
