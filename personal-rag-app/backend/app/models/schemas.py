from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class Message(BaseModel):
    """Single message in conversation history"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = None  # [{"role": "user", "content": "..."}, ...]


class Source(BaseModel):
    content: str
    source: str
    score: Optional[float] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class IngestRequest(BaseModel):
    document_path: str


class IngestResponse(BaseModel):
    success: bool
    documents_processed: int
    chunks_created: int
