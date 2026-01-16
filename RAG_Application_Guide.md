# Personal RAG Application - Production Build

A production-grade Retrieval-Augmented Generation (RAG) application with **Next.js frontend** and **Python FastAPI backend**, trained on your personal data.

**🎯 Perfect for Portfolio | Deployable | Scalable**

---

## 📋 Overview

### What You're Building
A professional AI-powered personal assistant that:
- Answers questions about your background, skills, and experience
- Uses your CV, LinkedIn posts, and portfolio as knowledge base
- Features a modern, responsive chat interface
- Deploys to production (Vercel + Railway/Render)

### Tech Stack
| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend | Python 3.11+, FastAPI, LangChain |
| Vector DB | ChromaDB (dev) / Pinecone (production) |
| LLM | OpenAI GPT-4 / GPT-4-turbo |
| Deployment | Vercel (frontend) + Railway/Render (backend) |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│                    (Next.js + Vercel)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Chat UI    │  │  Typewriter │  │  Message History    │ │
│  │  Component  │  │  Effect     │  │  (Local Storage)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │ REST API / Streaming
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                              │
│                (FastAPI + Railway/Render)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  API Routes │  │  RAG Chain  │  │  Document Ingestion │ │
│  │  /api/chat  │  │  LangChain  │  │  Pipeline           │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Vector Store (Pinecone/Chroma)         │   │
│  │              Embeddings: OpenAI ada-002             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Prerequisites

### Required Tools
- **Node.js** 18+ (for Next.js frontend)
- **Python** 3.11+
- **Git** (version control)
- **OpenAI API Key**
- **Pinecone API Key** (free tier available for production)

### Development Tools
- VS Code with Python & TypeScript extensions
- Postman or Thunder Client (API testing)
- Docker (optional, for containerization)

---

## 📁 Project Structure

```
personal-rag-app/
├── frontend/                    # Next.js Application
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx            # Landing page
│   │   ├── chat/
│   │   │   └── page.tsx        # Chat interface
│   │   ├── api/
│   │   │   └── chat/
│   │   │       └── route.ts    # API proxy (optional)
│   │   └── globals.css
│   ├── components/
│   │   ├── ChatWindow.tsx
│   │   ├── ChatMessage.tsx
│   │   ├── ChatInput.tsx
│   │   ├── TypingIndicator.tsx
│   │   └── Sidebar.tsx
│   ├── lib/
│   │   └── api.ts              # API client
│   ├── hooks/
│   │   └── useChat.ts          # Chat logic hook
│   ├── types/
│   │   └── index.ts
│   ├── public/
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── package.json
│   └── .env.local
│
├── backend/                     # Python FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI entry point
│   │   ├── config.py           # Settings & env vars
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── chat.py         # Chat endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── rag_service.py  # RAG chain logic
│   │   │   ├── vectorstore.py  # Vector DB operations
│   │   │   └── embeddings.py   # Embedding service
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py      # Pydantic models
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── document_loader.py
│   ├── scripts/
│   │   └── ingest_documents.py # Data ingestion script
│   ├── data/
│   │   └── personal/           # Your documents
│   ├── tests/
│   │   └── test_rag.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
│
├── docs/                        # Documentation
│   └── API.md
├── docker-compose.yml          # Local development
├── .gitignore
└── README.md
```

---

## � Part 1: Backend Setup (Python FastAPI)

### Step 1.1: Initialize Backend

```bash
# Create project directory
mkdir -p personal-rag-app/backend
cd personal-rag-app/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create requirements.txt
```

### Step 1.2: Requirements (requirements.txt)

```txt
# Core
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-dotenv==1.0.0
pydantic==2.5.3
pydantic-settings==2.1.0

# LangChain
langchain==0.1.0
langchain-openai==0.0.3
langchain-community==0.0.12

# Vector Stores
chromadb==0.4.22
pinecone-client==3.0.0

# Document Processing
pypdf==3.17.4
docx2txt==0.8
unstructured==0.12.0
tiktoken==0.5.2

# API & CORS
python-multipart==0.0.6

# Production
gunicorn==21.2.0
```

```bash
pip install -r requirements.txt
```

### Step 1.3: Configuration (app/config.py)

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "personal-rag"
    
    # App Settings
    app_name: str = "Personal RAG API"
    debug: bool = False
    
    # RAG Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retriever_k: int = 5
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
```

### Step 1.4: Pydantic Schemas (app/models/schemas.py)

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None


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
```

### Step 1.5: Vector Store Service (app/services/vectorstore.py)

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from app.config import get_settings
import os

settings = get_settings()


class VectorStoreService:
    _instance = None
    _vectorstore = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key
        )
    
    def get_vectorstore(self, use_pinecone: bool = True):
        """Get or create vector store instance."""
        if self._vectorstore is not None:
            return self._vectorstore
        
        if use_pinecone and settings.pinecone_api_key:
            # Production: Use Pinecone
            pc = Pinecone(api_key=settings.pinecone_api_key)
            self._vectorstore = PineconeVectorStore(
                index=pc.Index(settings.pinecone_index_name),
                embedding=self.embeddings,
                text_key="text"
            )
        else:
            # Development: Use Chroma
            self._vectorstore = Chroma(
                persist_directory="./chroma_db",
                embedding_function=self.embeddings
            )
        
        return self._vectorstore
    
    def get_retriever(self):
        """Get retriever with configured settings."""
        vectorstore = self.get_vectorstore()
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": settings.retriever_k}
        )


vectorstore_service = VectorStoreService()
```

### Step 1.6: RAG Service (app/services/rag_service.py)

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from app.services.vectorstore import vectorstore_service
from app.config import get_settings
from typing import Dict, Any
import uuid

settings = get_settings()


class RAGService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.3,
            openai_api_key=settings.openai_api_key,
            streaming=True
        )
        self._chain = None
    
    def _get_prompt(self) -> ChatPromptTemplate:
        """Create the RAG prompt template."""
        system_prompt = """You are a helpful AI assistant representing a professional.
You answer questions about their background, skills, experience, and projects 
based on their personal documents (CV, LinkedIn posts, portfolio).

IMPORTANT GUIDELINES:
1. Use ONLY the provided context to answer questions
2. If information isn't in the context, say "I don't have that specific information"
3. Be professional, friendly, and represent the person positively
4. For technical questions, provide detailed answers from their experience
5. When discussing projects, highlight achievements and technologies used
6. Keep responses concise but informative

Context from personal documents:
{context}
"""
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])
    
    def get_chain(self):
        """Get or create the RAG chain."""
        if self._chain is not None:
            return self._chain
        
        retriever = vectorstore_service.get_retriever()
        prompt = self._get_prompt()
        
        question_answer_chain = create_stuff_documents_chain(
            self.llm, prompt
        )
        self._chain = create_retrieval_chain(
            retriever, question_answer_chain
        )
        
        return self._chain
    
    async def get_answer(self, question: str, session_id: str = None) -> Dict[str, Any]:
        """Process a question and return answer with sources."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        chain = self.get_chain()
        response = chain.invoke({"input": question})
        
        # Extract sources
        sources = []
        for doc in response.get("context", []):
            sources.append({
                "content": doc.page_content[:200] + "...",
                "source": doc.metadata.get("source", "Unknown"),
                "score": doc.metadata.get("score")
            })
        
        return {
            "answer": response["answer"],
            "sources": sources,
            "session_id": session_id
        }


rag_service = RAGService()
```

### Step 1.7: Chat Router (app/routers/chat.py)

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse, HealthResponse
from app.services.rag_service import rag_service
from datetime import datetime
import json

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message and return AI response.
    
    - **message**: The user's question about the person
    - **session_id**: Optional session ID for conversation tracking
    """
    try:
        result = await rag_service.get_answer(
            question=request.message,
            session_id=request.session_id
        )
        
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            session_id=result["session_id"],
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response for real-time typing effect.
    """
    async def generate():
        try:
            result = await rag_service.get_answer(
                question=request.message,
                session_id=request.session_id
            )
            
            # Stream the answer word by word
            words = result["answer"].split()
            for word in words:
                yield f"data: {json.dumps({'token': word + ' '})}\n\n"
            
            # Send final message with sources
            yield f"data: {json.dumps({'done': True, 'sources': result['sources']})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

### Step 1.8: Main Application (app/main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat
from app.config import get_settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered personal assistant API using RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "https://your-domain.vercel.app"  # Add your Vercel domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Personal RAG API...")
    logger.info(f"📚 Debug mode: {settings.debug}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Shutting down Personal RAG API...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
```

### Step 1.9: Document Ingestion Script (scripts/ingest_documents.py)

```python
"""
Document Ingestion Script
Run this to process and embed your personal documents.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import argparse

load_dotenv()


def load_documents(data_dir: str):
    """Load all documents from the data directory."""
    print(f"📂 Loading documents from {data_dir}...")
    
    documents = []
    
    # Load PDFs
    try:
        pdf_loader = DirectoryLoader(
            data_dir, glob="**/*.pdf", loader_cls=PyPDFLoader
        )
        documents.extend(pdf_loader.load())
        print(f"  ✅ Loaded PDF files")
    except Exception as e:
        print(f"  ⚠️ Error loading PDFs: {e}")
    
    # Load text files
    try:
        txt_loader = DirectoryLoader(
            data_dir, glob="**/*.txt", loader_cls=TextLoader
        )
        documents.extend(txt_loader.load())
        print(f"  ✅ Loaded TXT files")
    except Exception as e:
        print(f"  ⚠️ Error loading TXT: {e}")
    
    # Load markdown files
    try:
        md_loader = DirectoryLoader(
            data_dir, glob="**/*.md", loader_cls=UnstructuredMarkdownLoader
        )
        documents.extend(md_loader.load())
        print(f"  ✅ Loaded MD files")
    except Exception as e:
        print(f"  ⚠️ Error loading MD: {e}")
    
    print(f"📄 Total documents loaded: {len(documents)}")
    return documents


def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    """Split documents into chunks."""
    print(f"✂️ Splitting documents (chunk_size={chunk_size})...")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = splitter.split_documents(documents)
    print(f"📦 Created {len(chunks)} chunks")
    return chunks


def create_embeddings():
    """Create OpenAI embeddings instance."""
    return OpenAIEmbeddings(
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )


def ingest_to_chroma(chunks, embeddings, persist_dir="./chroma_db"):
    """Ingest chunks to local Chroma database."""
    print(f"💾 Ingesting to Chroma at {persist_dir}...")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    
    print("✅ Chroma ingestion complete!")
    return vectorstore


def ingest_to_pinecone(chunks, embeddings):
    """Ingest chunks to Pinecone (production)."""
    print("🌲 Ingesting to Pinecone...")
    
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "personal-rag")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=api_key)
    
    # Create index if it doesn't exist
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing_indexes:
        print(f"  Creating index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=1536,  # OpenAI embedding dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    
    # Ingest documents
    vectorstore = PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        index_name=index_name
    )
    
    print("✅ Pinecone ingestion complete!")
    return vectorstore


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into vector store")
    parser.add_argument(
        "--data-dir",
        default="./data/personal",
        help="Directory containing personal documents"
    )
    parser.add_argument(
        "--target",
        choices=["chroma", "pinecone", "both"],
        default="chroma",
        help="Target vector store"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Chunk size for text splitting"
    )
    
    args = parser.parse_args()
    
    print("🚀 Starting document ingestion...")
    print("=" * 50)
    
    # Load and process documents
    documents = load_documents(args.data_dir)
    
    if not documents:
        print("❌ No documents found! Please add documents to the data directory.")
        return
    
    chunks = split_documents(documents, chunk_size=args.chunk_size)
    embeddings = create_embeddings()
    
    # Ingest based on target
    if args.target in ["chroma", "both"]:
        ingest_to_chroma(chunks, embeddings)
    
    if args.target in ["pinecone", "both"]:
        ingest_to_pinecone(chunks, embeddings)
    
    print("=" * 50)
    print("🎉 Ingestion complete!")


if __name__ == "__main__":
    main()
```

### Step 1.10: Backend Environment (.env)

```env
# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Pinecone (Production)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=personal-rag

# App
DEBUG=true
FRONTEND_URL=http://localhost:3000
```

### Step 1.11: Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

---

## 🎨 Part 2: Frontend Setup (Next.js)

### Step 2.1: Initialize Next.js Project

```bash
cd personal-rag-app

# Create Next.js app with TypeScript and Tailwind
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*"

cd frontend
```

### Step 2.2: Install Additional Dependencies

```bash
# UI Components
npm install lucide-react clsx tailwind-merge
npm install framer-motion  # Animations

# State management & utilities  
npm install zustand  # Lightweight state
npm install uuid
npm install @types/uuid --save-dev
```

### Step 2.3: Types (types/index.ts)

```typescript
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
}

export interface Source {
  content: string;
  source: string;
  score?: number;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  session_id: string;
  timestamp: string;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  sessionId: string | null;
  error: string | null;
}
```

### Step 2.4: API Client (lib/api.ts)

```typescript
import { ChatResponse } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function sendMessage(message: string, sessionId?: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}
```

### Step 2.5: Chat Hook (hooks/useChat.ts)

```typescript
'use client';

import { useState, useCallback } from 'react';
import { Message, ChatState } from '@/types';
import { sendMessage } from '@/lib/api';
import { v4 as uuidv4 } from 'uuid';

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    sessionId: null,
    error: null,
  });

  const addMessage = useCallback((role: 'user' | 'assistant', content: string, sources?: any[]) => {
    const newMessage: Message = {
      id: uuidv4(),
      role,
      content,
      timestamp: new Date(),
      sources,
    };

    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, newMessage],
    }));

    return newMessage;
  }, []);

  const send = useCallback(async (content: string) => {
    if (!content.trim() || state.isLoading) return;

    // Add user message
    addMessage('user', content);

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await sendMessage(content, state.sessionId || undefined);

      // Add assistant message
      addMessage('assistant', response.answer, response.sources);

      setState((prev) => ({
        ...prev,
        sessionId: response.session_id,
        isLoading: false,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Something went wrong',
      }));
    }
  }, [state.isLoading, state.sessionId, addMessage]);

  const clearChat = useCallback(() => {
    setState({
      messages: [],
      isLoading: false,
      sessionId: null,
      error: null,
    });
  }, []);

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    send,
    clearChat,
  };
}
```

### Step 2.6: Chat Components

#### ChatMessage Component (components/ChatMessage.tsx)

```tsx
'use client';

import { Message } from '@/types';
import { User, Bot, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { motion } from 'framer-motion';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-blue-600' : 'bg-gradient-to-br from-purple-600 to-pink-600'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex flex-col max-w-[80%] ${isUser ? 'items-end' : ''}`}>
        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? 'bg-blue-600 text-white rounded-tr-sm'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white rounded-tl-sm'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              {showSources ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              {message.sources.length} sources
            </button>

            {showSources && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-2 space-y-2"
              >
                {message.sources.map((source, idx) => (
                  <div
                    key={idx}
                    className="text-xs p-2 bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700"
                  >
                    <p className="font-medium text-gray-600 dark:text-gray-400">
                      {source.source}
                    </p>
                    <p className="text-gray-500 mt-1 line-clamp-2">{source.content}</p>
                  </div>
                ))}
              </motion.div>
            )}
          </div>
        )}

        {/* Timestamp */}
        <span className="text-xs text-gray-400 mt-1">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </motion.div>
  );
}
```

#### ChatInput Component (components/ChatInput.tsx)

```tsx
'use client';

import { useState, KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, isLoading, placeholder }: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
      <div className="flex items-end gap-2 max-w-4xl mx-auto">
        <div className="flex-1 relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || "Ask me anything about my background..."}
            rows={1}
            className="w-full resize-none rounded-xl border border-gray-300 dark:border-gray-600 
                       bg-gray-50 dark:bg-gray-800 px-4 py-3 pr-12 
                       text-gray-900 dark:text-white placeholder-gray-500
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       transition-all duration-200"
            style={{ minHeight: '48px', maxHeight: '200px' }}
          />
        </div>

        <button
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          className="flex-shrink-0 w-12 h-12 rounded-xl bg-blue-600 hover:bg-blue-700 
                     disabled:bg-gray-300 dark:disabled:bg-gray-700
                     text-white flex items-center justify-center
                     transition-colors duration-200"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>

      <p className="text-center text-xs text-gray-400 mt-2">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  );
}
```

#### ChatWindow Component (components/ChatWindow.tsx)

```tsx
'use client';

import { useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { useChat } from '@/hooks/useChat';
import { Sparkles, MessageSquare, Trash2 } from 'lucide-react';

export function ChatWindow() {
  const { messages, isLoading, error, send, clearChat } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-gray-900">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-gray-900 dark:text-white">
              Personal AI Assistant
            </h1>
            <p className="text-sm text-gray-500">
              Ask me anything about my background
            </p>
          </div>
        </div>

        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="p-2 text-gray-400 hover:text-red-500 transition-colors"
            title="Clear chat"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        )}
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <MessageSquare className="w-16 h-16 text-gray-300 dark:text-gray-600 mb-4" />
            <h2 className="text-xl font-medium text-gray-900 dark:text-white mb-2">
              Welcome! 👋
            </h2>
            <p className="text-gray-500 max-w-md mb-6">
              I'm an AI assistant trained on personal documents. Ask me about 
              skills, experience, projects, or background!
            </p>

            {/* Suggested Questions */}
            <div className="flex flex-wrap gap-2 justify-center max-w-lg">
              {[
                "What are your technical skills?",
                "Tell me about your projects",
                "What's your experience?",
                "Summarize your background",
              ].map((question) => (
                <button
                  key={question}
                  onClick={() => send(question)}
                  className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-800 
                             text-gray-700 dark:text-gray-300 rounded-full
                             hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            {/* Error message */}
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput onSend={send} isLoading={isLoading} />
    </div>
  );
}
```

### Step 2.7: Main Page (app/page.tsx)

```tsx
import { ChatWindow } from '@/components/ChatWindow';

export default function Home() {
  return (
    <main className="h-screen">
      <ChatWindow />
    </main>
  );
}
```

### Step 2.8: Layout (app/layout.tsx)

```tsx
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Personal AI Assistant | Your Name',
  description: 'AI-powered assistant trained on my professional background, skills, and experience.',
  keywords: ['AI', 'Portfolio', 'RAG', 'Personal Assistant'],
  authors: [{ name: 'Your Name' }],
  openGraph: {
    title: 'Personal AI Assistant',
    description: 'Ask me anything about my professional background!',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} antialiased`}>
        {children}
      </body>
    </html>
  );
}
```

### Step 2.9: Global Styles (app/globals.css)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 0, 0, 0;
  --background-rgb: 255, 255, 255;
}

@media (prefers-color-scheme: dark) {
  :root {
    --foreground-rgb: 255, 255, 255;
    --background-rgb: 17, 24, 39;
  }
}

body {
  color: rgb(var(--foreground-rgb));
  background: rgb(var(--background-rgb));
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

@media (prefers-color-scheme: dark) {
  ::-webkit-scrollbar-thumb {
    background: #475569;
  }
  
  ::-webkit-scrollbar-thumb:hover {
    background: #64748b;
  }
}
```

### Step 2.10: Frontend Environment (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 Part 3: Deployment

### Step 3.1: Deploy Backend to Railway

#### Option A: Railway (Recommended)

1. **Create Railway Account**: https://railway.app

2. **Install Railway CLI**:
```bash
npm install -g @railway/cli
railway login
```

3. **Deploy Backend**:
```bash
cd backend
railway init
railway up
```

4. **Set Environment Variables** (Railway Dashboard):
```
OPENAI_API_KEY=sk-xxx
PINECONE_API_KEY=xxx
PINECONE_INDEX_NAME=personal-rag
FRONTEND_URL=https://your-app.vercel.app
DEBUG=false
```

5. **Get Backend URL**: `https://your-backend.railway.app`

#### Option B: Render

1. Create account at https://render.com
2. Connect GitHub repository
3. Create new "Web Service"
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT`
5. Add environment variables

### Step 3.2: Deploy Frontend to Vercel

1. **Push to GitHub**:
```bash
cd frontend
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/personal-rag-frontend.git
git push -u origin main
```

2. **Deploy on Vercel**:
   - Go to https://vercel.com
   - Import your GitHub repository
   - Configure environment variables:
     ```
     NEXT_PUBLIC_API_URL=https://your-backend.railway.app
     ```
   - Deploy!

3. **Custom Domain** (Optional):
   - Add your domain in Vercel settings
   - Update DNS records

### Step 3.3: Production Checklist

```markdown
## Pre-Deployment Checklist

### Backend
- [ ] All environment variables set
- [ ] CORS configured for production domain
- [ ] Rate limiting implemented
- [ ] Error handling tested
- [ ] Health endpoint working
- [ ] Pinecone index created and populated

### Frontend
- [ ] API URL pointing to production backend
- [ ] Meta tags configured (SEO)
- [ ] Favicon and OG images added
- [ ] Error boundaries implemented
- [ ] Loading states working
- [ ] Mobile responsive

### Security
- [ ] API keys secured (not in code)
- [ ] HTTPS enabled
- [ ] Input validation on both ends
- [ ] Rate limiting to prevent abuse

### Testing
- [ ] API endpoints tested
- [ ] Chat functionality working
- [ ] Source citations showing
- [ ] Error handling graceful
```

---

## 📊 Part 4: Data Organization

### Step 4.1: Prepare Your Personal Data

Create this folder structure in `backend/data/personal/`:

```
data/personal/
├── cv/
│   └── resume.pdf           # Your resume/CV
├── linkedin/
│   ├── profile.txt          # LinkedIn About section
│   ├── experience.txt       # Work experience descriptions
│   └── posts.txt            # Your LinkedIn posts
├── portfolio/
│   ├── about.md             # About me content
│   ├── projects.md          # Project descriptions
│   └── skills.md            # Skills breakdown
├── blog/
│   └── articles.md          # Blog posts (if any)
└── additional/
    ├── achievements.txt     # Awards, certifications
    ├── education.txt        # Detailed education
    └── recommendations.txt  # Recommendations/testimonials
```

### Step 4.2: Sample Data Templates

#### profile.txt
```
PROFESSIONAL SUMMARY
---
[Your Name] is a [Title] with [X] years of experience in [Domain].
Currently working at [Company] focusing on [Focus Area].

KEY HIGHLIGHTS
---
- Led development of [Project] resulting in [Outcome]
- Expert in [Technology 1], [Technology 2], [Technology 3]
- Published [X] articles on [Topic]
- Speaker at [Conference/Event]

CONTACT
---
- Email: your@email.com
- LinkedIn: linkedin.com/in/yourprofile
- GitHub: github.com/yourusername
- Portfolio: yourwebsite.com
```

#### projects.md
```markdown
# Projects Portfolio

## Project 1: [Project Name]
**Duration**: Jan 2024 - Present
**Role**: Lead Developer
**Technologies**: Python, React, AWS

### Description
[Detailed description of the project]

### Key Achievements
- Implemented [Feature] improving [Metric] by [X]%
- Reduced [Process] time from [X] to [Y]
- Led team of [X] developers

### Links
- GitHub: [Link]
- Live Demo: [Link]

---

## Project 2: [Project Name]
[Similar structure]
```

### Step 4.3: Run Ingestion

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Run ingestion (local development)
python scripts/ingest_documents.py --data-dir ./data/personal --target chroma

# Run ingestion (production - Pinecone)
python scripts/ingest_documents.py --data-dir ./data/personal --target pinecone
```

---

## 🔧 Part 5: Local Development

### Step 5.1: Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Backend running at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### Step 5.2: Start Frontend

```bash
cd frontend
npm run dev
```

Frontend running at: `http://localhost:3000`

### Step 5.3: Docker Compose (Optional)

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - FRONTEND_URL=http://localhost:3000
    volumes:
      - ./backend/data:/app/data
      - ./backend/chroma_db:/app/chroma_db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
```

Run with:
```bash
docker-compose up --build
```

---

## 🎯 Part 6: Testing & Quality

### Step 6.1: Backend Tests (tests/test_rag.py)

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chat_endpoint():
    response = client.post(
        "/api/chat",
        json={"message": "What are your skills?"}
    )
    assert response.status_code == 200
    assert "answer" in response.json()


def test_chat_empty_message():
    response = client.post(
        "/api/chat",
        json={"message": ""}
    )
    assert response.status_code == 422  # Validation error


def test_chat_with_session():
    # First message
    response1 = client.post(
        "/api/chat",
        json={"message": "Tell me about yourself"}
    )
    session_id = response1.json()["session_id"]
    
    # Follow-up with session
    response2 = client.post(
        "/api/chat",
        json={"message": "What else?", "session_id": session_id}
    )
    assert response2.json()["session_id"] == session_id
```

Run tests:
```bash
cd backend
pytest tests/ -v
```

### Step 6.2: Sample Questions for Testing

```markdown
## Test Questions

### Basic Info
- "Who are you?"
- "What is your background?"
- "Tell me about yourself"

### Skills
- "What programming languages do you know?"
- "What are your technical skills?"
- "What tools and technologies do you use?"

### Experience
- "Where have you worked?"
- "What is your work experience?"
- "Tell me about your current role"

### Projects
- "What projects have you built?"
- "Tell me about your most impressive project"
- "What was your role in [specific project]?"

### Education
- "What is your educational background?"
- "Where did you study?"
- "What certifications do you have?"

### Edge Cases
- "What's your favorite color?" (should handle gracefully)
- "Tell me about something not in your documents"
- Very long question...
```

---

## 🎨 Part 7: Customization Ideas

### UI Enhancements
- Add dark/light mode toggle
- Add avatar/profile picture
- Add typing animation for responses
- Add sound effects for new messages
- Add markdown rendering for responses

### Functionality
- Add conversation history (persist to localStorage)
- Add export chat as PDF
- Add share conversation feature
- Add feedback buttons (thumbs up/down)
- Add suggested follow-up questions

### Advanced RAG
- Add hybrid search (BM25 + semantic)
- Add re-ranking with cross-encoders
- Add conversation memory for context
- Add citation links to source documents

---

## ✅ Final Checklist

### Setup Complete
- [ ] Backend folder structure created
- [ ] Frontend folder structure created
- [ ] Dependencies installed
- [ ] Environment variables configured

### Data Ready
- [ ] Personal documents organized
- [ ] Documents ingested to vector store
- [ ] Test queries working

### Development
- [ ] Backend API running locally
- [ ] Frontend running locally
- [ ] Chat functionality working
- [ ] Sources displaying correctly

### Deployment
- [ ] Backend deployed (Railway/Render)
- [ ] Frontend deployed (Vercel)
- [ ] CORS configured correctly
- [ ] Production environment variables set
- [ ] Custom domain configured (optional)

### Polish
- [ ] SEO meta tags added
- [ ] Favicon added
- [ ] OG image created
- [ ] Mobile responsive tested
- [ ] Error handling tested

---

## 🎯 Example Test Queries

1. "What is your educational background?"
2. "What programming languages do you know?"
3. "Summarize your work experience."
4. "What projects have you built?"
5. "What are your key achievements?"
6. "Why should someone hire you?"
7. "What is your expertise in [specific technology]?"

---

## 📚 Resources

- [LangChain Documentation](https://python.langchain.com/docs/)
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Vercel Deployment](https://vercel.com/docs)
- [Railway Deployment](https://docs.railway.app/)

---

## 📧 Support

If you have questions while building this project, refer to the documentation links above or check the GitHub issues for common problems.

---

*Guide Created: January 2026*
*Stack: Next.js 14 + FastAPI + LangChain + Pinecone*
