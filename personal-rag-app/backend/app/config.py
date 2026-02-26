from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Keys
    huggingface_api_key: str = ""  # For embeddings (sentence-transformers)
    groq_api_key: str = ""  # FREE from https://console.groq.com
    tavily_api_key: str = ""  # FREE from https://app.tavily.com
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "personal-rag"
    
    # Groq LLM Settings
    groq_model: str = "llama-3.3-70b-versatile"
    
    # GitHub
    github_username: str = "iamabdullah1"
    
    # App Settings
    app_name: str = "Personal RAG API"
    debug: bool = False
    
    # RAG Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retriever_k: int = 3
    max_tokens: int = 800
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
