import os
from typing import Dict, ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path 

class Settings(BaseSettings):
    """
    제목: 애플리케이션 환경 설정 클래스
    목적: DB, Elasticsearch, 크롤링, PDF, NLP 모델 관련 설정 중앙 관리
    핵심동작: 환경 변수 또는 기본값을 로드하여 전역 설정 객체 생성
    """
    
    # -- Mysql --
    # Database URL
    # Docker의 environment 섹션에 있는 값들을 자동으로 읽어옴
    DATABASE_URL: str = "mysql+aiomysql://ngms:ms123@shared_mysql_db:3306/PolitiSearch"

    # -- Elasticsearch --
    # Elasticsearch 설정
    ELASTICSEARCH_URL: str = "http://elasticsearch:9200"
    ELASTIC_USERNAME: str = ""
    ELASTIC_PASSWORD: str = ""


    # -- NationalAssembly --
    NA_BASE_URL: str = "https://www.assembly.go.kr"
    NA_MAIN_URL: str = "/portal/main/contents.do?menuNo=600045"
    NA_API_URL: str = "/portal/cnts/cntsCmmit/listMtgRcord.json"

    # -- PDF 저장 경로 --
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # app 폴더 상위
    ROOT_DIR: str=  os.path.dirname(BASE_DIR) # 프로젝트 루트 (/app)
    PDF_DIR: str= os.path.join(ROOT_DIR, "static", "pdfs")


    # -- Docker 컨테이너 내부 파일 시스템 기준 경로 --
    CONTAINER_ROOT_PATH: ClassVar[Path] = Path("/app/static/pdfs")

    # -- SentenceTransformer에서 사용할 모델 이름 --
    EMBEDDING_MODEL_NAME: str= "jhgan/ko-sbert-nli"
    DEBUG: bool = False

    # -- SBERT --
    SBERT_MODEL_PATH: str = "/app/app/ko-sbert"

    # KeyBERT 기반 키워드 추출 품질 조절
    # 다양성 및 상위 키워드 개수 설정
    KEYBERT_DIVERSITY: float = 0.3
    KEYBERT_TOP_N: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    

# 애플리케이션 전반에서 공통 설정 접근 제공
settings = Settings()