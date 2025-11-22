from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.document import Document
from app.schema.crawler import DocumentCreate

class NationalAssemblyCrawlerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db 
    

    # ----------------------------------------
    # 1. 중복 체크 (이미 수집된 ID인가?)
    # ----------------------------------------
    async def is_crawled(self, file_id: str) -> bool:
        """
        doc_id(문서 고유번호)가 DB에 존재하는지 확인
        """
        stmt = select(Document).where(Document.file_id == file_id)
        result = await self.db.execute(stmt)

        return result.scalar_one_or_none() is not None 
    

    # ----------------------------------------
    # 2. 문서 정보 저장 (INSERT)
    # ----------------------------------------
    async def save_document(self, doc_data: DocumentCreate) -> int:
        """
        크롤링한 문서 정보를 DB에 저장
        """
        document = Document(
            parliament = doc_data["parliament"],
            meeting_series = doc_data["meeting_series"],
            meeting_number = doc_data["meeting_number"],
            title = doc_data["title"],
            file_id  = doc_data["file_id"],
            file_url = doc_data["file_url"],
            file_path  = doc_data["file_path"],
            meeting_date = doc_data["meeting_date"]
        )

        try: 
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)
            return document.id 
        except IntegrityError:
            await self.db.rollback()
            print("[DB Error] 중복된 문서 ID입니다: {doc_data['doc_id']}")
            return -1 
        except Exception as e:
            await self.db.rollback()
            print(f"[DB Error] 저장 실패: {e}")
            raise e