from pydantic_settings import BaseSettings 

class Settings(BaseSettings):
    
    # Docker의 environment 섹션에 있는 값들을 자동으로 읽어옴
    DATABASE_URL: str 

    #Elasticsearch 설정
    ELASTICSEARCH_HOST: str = "http://elasticsearch:9200"
    ELASTIC_USERNAME: str = ""
    ELASTIC_PASSWORD: str = ""

    DEBUG: bool = False 

    class Config: 
        # .env 파일 위치 지정
        env_file = ".env"
    

settings = Settings()

