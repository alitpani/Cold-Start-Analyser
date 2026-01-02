from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Cold Start Analyzer"
    
    # Environment
    APP_ENV: str = "development"
    
    # Database
    DATABASE_URL: str
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://app.coldstart.dev"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
