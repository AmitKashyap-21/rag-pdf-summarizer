from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "RAG PDF Summarizer"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_LLM_MODEL: str = "openai/gpt-3.5-turbo"
    OPENROUTER_EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_TIMEOUT: int = 30
    OPENROUTER_MAX_RETRIES: int = 3

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/rag_pdf"

    STORAGE_PATH: str = "./uploads"
    INDEXES_PATH: str = "./indexes"
    MAX_FILE_SIZE_MB: int = 50

    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    FAISS_METRIC: str = "L2"

    API_KEY: str = "changeme"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
