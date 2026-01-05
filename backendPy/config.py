 # config.py
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    MONGODB_URI: str
    DB_NAME: str = "LegalEase_FYP"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 100000

    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"
    OPENROUTER_MODEL: str = "mistralai/mistral-7b-instruct:free"

    UPLOAD_DIR: str = "uploads"
    INDEX_DIR: str = "indexes"
    CHUNKS_DIR: str = "chunks"
    MAX_CHUNKS_FETCH: int = 10

    class Config:
        env_file = ".env"

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.INDEX_DIR, exist_ok=True)
os.makedirs(settings.CHUNKS_DIR, exist_ok=True)
