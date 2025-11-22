from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# DB 모델 임포트 (모델 파일 경로에 맞게 수정하세요)
from app.models.documents import Document  

class NationalAssemblyCrawlerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----------------------------------------
    # 1. 중복 체크 (이미 수집된 ID인가?)
    # ----------------------------------------
    async def is_crawled(self, doc_id: str) -> bool:
        """
        doc_id(문서 고유번호)가 DB에 존재하는지 확인합니다.
        존재하면 True, 없으면 False 반환
        """
        stmt = select(Document).where(Document.doc_id == doc_id)
        result = await self.db.execute(stmt)
        
        # scalar_one_or_none(): 결과가 1개면 객체 반환, 없으면 None 반환
        return result.scalar_one_or_none() is not None

    # ----------------------------------------
    # 2. 문서 정보 저장 (INSERT)
    # ----------------------------------------
    async def save_document(self, doc_data: dict) -> int:
        """
        크롤링한 문서 정보를 DB에 저장합니다.
        doc_data: 딕셔너리 형태의 데이터
        """
        # Pydantic 모델이나 Dict를 DB 모델 객체로 변환
        # (만약 doc_data에 모델에 없는 키가 있다면 pop 해주거나 **kwargs 처리)
        document = Document(
            doc_id=doc_data["doc_id"],
            committee_name=doc_data.get("committee_name"),
            title=doc_data["title"],
            meeting_date=doc_data.get("meeting_date"),
            file_path=doc_data.get("file_path"),
            file_url=doc_data.get("file_url"),
            
        )

        try:
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document) # 저장 후 ID(PK) 값 갱신
            return document.id
            
        except IntegrityError:
            # 혹시 모를 동시성 이슈로 중복 에러 발생 시 롤백
            await self.db.rollback()
            print(f"⚠️ [DB Error] 중복된 문서 ID입니다: {doc_data['doc_id']}")
            return -1
        except Exception as e:
            await self.db.rollback()
            print(f"⚠️ [DB Error] 저장 실패: {e}")
            raise e