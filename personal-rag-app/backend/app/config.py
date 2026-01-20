from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Keys
    huggingface_api_key: str = ""  # Get FREE from https://huggingface.co/settings/tokens
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "personal-rag"
    
    # App Settings
    app_name: str = "Personal RAG API"
    debug: bool = False
    
    # RAG Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retriever_k: int = 3
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
