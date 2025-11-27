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
    def __init__(self, db_p03_track_b: PdfEmbeddingExtractorRepository):
        """
        model_name: 사용할 SentenceTransformer 모델 이름
        """
        self.db_repo = db_p03_track_b
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, device="cpu")

    # -------------------------
    #       [메인 함수]
    # -------------------------
    async def run_embedding_extraction(self, limit: int = 5):
        """
        벡터가 없는 세그먼트 조회 -> 임베딩 -> 저장
        """
        # -- [Step 1] 대상 조회
        target_segments = await self.db_repo.get_segments_without_vector(limit)

        if not target_segments:
            print("[Track B] 처리할 세그먼트가 없습니다.")
            return
        
        print(f"---------- [Track B] {len(target_segments)}개 세그먼트 임베딩 시작 ----------")


        # -- [Step 2] 비동기 임베딩 실행(CPU Bound) --
        # to_thread로 CPU 작업 분리
        processed_data = await asyncio.to_thread(self._process_segments_embedding, target_segments)

        # -- [Step 3] DB 업데이트 --
        await self.db_repo.update_vectors_bulk(processed_data)
        print(f"총 {len(processed_data)}건 임베딩 및 저장 완료")

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

        print(result_list)
        return result_list
