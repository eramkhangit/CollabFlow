from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field
from typing import List
from urllib.parse import quote_plus
import urllib.parse

class Settings(BaseSettings):

    DB_HOST:str
    DB_NAME:str
    DB_PORT:int
    DB_USER:str
    DB_PASSWORD:str

    APP_NAME :str
    ALLOW_DOMAIN: List[str]
    APP_VERSION:str = Field(default="1.0.0")
    DEBUG:bool
    ENVIRONMENT: str = Field(default="development")  # production, staging, development

    LOG_LEVEL:str
    LOG_FORMAT:str
    ENV:str
    APP_PORT:int

    
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
    
    @property
    def DB_URL_ENCODED(self) -> str:
        """Get database URL with encoded password (use for development only)"""
        encoded_pswd = urllib.parse.quote_plus(self.DB_PASSWORD)
        return f"mysql+pymysql://{self.DB_USER}:{encoded_pswd}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def SAFE_DB_URL(self) -> str:
        """Choose appropriate URL based on environment"""
        if self.ENVIRONMENT == "production":
            return self.DB_URL  # No encoding for production
        return self.DB_URL_ENCODED  # Encoding for development

def get_settings():
    return Settings()

settings = get_settings() 