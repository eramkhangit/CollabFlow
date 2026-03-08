from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List
from urllib.parse import quote_plus

class Settings(BaseSettings):

    DB_HOST:str
    DB_NAME:str
    DB_PORT:int
    DB_USER:str
    DB_PASSWORD:str

    APP_NAME :str
    ALLOW_DOMAIN: List[str]
    APP_VERSION:int
    DEBUG:bool

    LOG_LEVEL:str
    LOG_FORMATE:str

    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False     
    )

    @property
    def DB_URL(self) -> str:
        encoded_pswd = quote_plus(self.DB_PASSWORD)
        url=f"mysql+pymysql://{self.DB_USER}:{encoded_pswd}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

        return url 

def get_settings():
    return Settings()

settings = get_settings()