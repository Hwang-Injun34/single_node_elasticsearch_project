from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    # Docker의 environment 섹션에 있는 값들을 자동으로 읽어옴
    DATABASE_URL: str 

    #Elasticsearch 설정
    ELASTICSEARCH_HOST: str = "http://elasticsearch:9200"
    ELASTIC_USERNAME: str = ""
    ELASTIC_PASSWORD: str = ""

    DEBUG: bool = False 

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    

settings = Settings()

