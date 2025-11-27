import os
from typing import Dict 
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    
    # -- Mysql --
    # Database URL
    # Docker의 environment 섹션에 있는 값들을 자동으로 읽어옴
    DATABASE_URL: str = "mysql+aiomysql://ngms:ms123@shared_mysql_db:3306/PolitiSearch"

    # -- Elasticsearch --
    # Elasticsearch 설정
    ELASTICSEARCH_HOST: str = "http://elasticsearch:9200"
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

    # -- SentenceTransformer에서 사용할 모델 이름 --
    EMBEDDING_MODEL_NAME: str= "jhgan/ko-sbert-nli"
    DEBUG: bool = False


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    

settings = Settings()

