---
title: Personal RAG Chatbot API
emoji: 🤖
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Personal RAG Application - Backend

## ✅ Setup Complete!

Your FastAPI backend has been successfully created with the following structure:

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings & configuration
│   ├── routers/
│   │   ├── __init__.py
│   │   └── chat.py          # Chat API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rag_service.py   # RAG chain logic
│   │   └── vectorstore.py   # Vector DB operations
│   └── models/
│       ├── __init__.py
│       └── schemas.py       # Pydantic models
├── scripts/
│   └── ingest_documents.py  # Document ingestion script
├── data/
│   └── personal/
│       └── profile.txt      # Sample document
├── requirements.txt
├── .env
└── run.py
```

## 🚀 Next Steps

### 1. Get Your OpenAI API Key
1. Go to: https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key and update `.env` file:
   ```env
   OPENAI_API_KEY=sk-proj-your-actual-key-here
   ```

### 2. Add Your Personal Documents
Add your personal documents to `data/personal/`:
- PDFs (resume, certificates)
- Text files (profile, bio)
- Markdown files (projects, blog posts)

### 3. Ingest Documents
```bash
cd /Users/apple/Desktop/My\ LLM && source .venv/bin/activate
cd personal-rag-app/backend
python scripts/ingest_documents.py --data-dir ./data/personal --target chroma
```

### 4. Start the API Server
```bash
cd /Users/apple/Desktop/My\ LLM && source .venv/bin/activate
cd personal-rag-app/backend
python run.py
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Test the API
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **Chat Endpoint**: http://localhost:8000/api/chat

### 6. Test with curl
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are your technical skills?"}'
```

## 📝 Features Implemented

✅ FastAPI backend with async support
✅ RAG implementation with LangChain
✅ ChromaDB for local vector storage
✅ Pinecone support for production
✅ CORS configuration for frontend
✅ Health check endpoint
✅ Chat endpoint with source citations
✅ Streaming chat endpoint
✅ Document ingestion script
✅ Environment configuration
✅ Automatic API documentation

## 🔧 Configuration

Edit `.env` to configure:
- API keys (OpenAI, Pinecone)
- RAG settings (chunk size, retriever k)
- CORS origins
- Debug mode

## 📚 API Endpoints

### GET /api/health
Health check endpoint

### POST /api/chat
Send a message and get AI response
```json
{
  "message": "What are your skills?",
  "session_id": "optional-session-id"
}
```

### POST /api/chat/stream
Stream chat response for real-time typing effect

## 🎯 Sample Questions to Test

- "What are your technical skills?"
- "Tell me about your work experience"
- "What projects have you built?"
- "What is your educational background?"
- "What certifications do you have?"

## 🔐 Important Notes

1. **Never commit** your `.env` file with real API keys
2. Add `.env` to `.gitignore`
3. Use environment variables in production
4. Update CORS origins for your production frontend

## 🐛 Troubleshooting

**Import errors**: Make sure you're in the virtual environment
```bash
cd /Users/apple/Desktop/My\ LLM && source .venv/bin/activate
```

**API key errors**: Update your `.env` file with valid API keys

**No documents found**: Add documents to `data/personal/` directory

**Module not found**: Reinstall requirements
```bash
uv pip install -r requirements.txt
```

## 📖 Next: Build the Frontend

Now that your backend is ready, you can:
1. Build a React frontend to interact with the API
2. Deploy backend to Railway/Render
3. Deploy frontend to Vercel
4. Add more documents for better responses

---

**Backend is ready! 🎉**
