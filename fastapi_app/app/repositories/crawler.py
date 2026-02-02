from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.document import Document
from app.models.document_processes import DocumentProcess, ProcessStatus
from app.schema.crawler import DocumentCreate


class NationalAssemblyCrawlerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db 

    async def commit(self):
        """
        제목: 트랜잭션 커밋
        목적: 현재 세션의 변경 사항 DB 반영
        핵심동작: commit() 호출
        """
        await self.db.commit()

    # ----------------------------------------
    # 1. 중복 체크 (이미 수집된 ID인가?)
    # ----------------------------------------
    async def is_crawled(self, conferNum: str) -> bool:
        """
        제목: 문서 중복 여부 확인
        목적: 이미 수집된 문서인지 사전 검증
        핵심동작: conferNum 기준 존재 여부 조회
        """
        stmt = select(Document).where(Document.conferNum == conferNum)
        result = await self.db.execute(stmt)

        return result.scalar_one_or_none() is not None 
    

    # ----------------------------------------
    # 2. 문서 정보 저장 (INSERT)
    # ----------------------------------------
    async def save_document_1(self, doc_data: DocumentCreate) -> int:
        """
        제목: 문서 단건 저장
        목적: 크롤링한 문서 메타데이터 DB 저장
        핵심동작: Document INSERT -> ID 변환
        """
        document = Document(
            className = doc_data["className"],
            committeeName= doc_data["committeeName"],
            confDate = doc_data["confDate"],
            conferNum = doc_data["conferNum"],
            pdfLinkUrl  = doc_data["pdfLinkUrl"],
            file_path  = doc_data["file_path"],
            title  = doc_data["title"]
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
        
    # ----------------------------------------
    # 3. Document & DocumentProcess 내용 저장
    # ----------------------------------------
    async def save_document(self, doc_data: dict) -> Document:
        """
        제목: 문서 및 처리 상태 초기화 저장
        목적: Document 저장과 동시에 처리 상태(PENDING) 생성
        핵심동작: Document INSERT -> DocumentProcess 생성 -> 커밋
        """
        # 1. Document 저장
        new_doc = Document(**doc_data)
        self.db.add(new_doc)

        # Flush를 호출하여 new_doc.id를 확보
        await self.db.flush()

        # 2. DocumentProcess 생성(초기 상태: PENDING)
        new_processs = DocumentProcess(
            document_id=new_doc.id,
            status=ProcessStatus.PENDING,
        )

        self.db.add(new_processs)

        await self.db.commit()
    