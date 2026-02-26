# Personal RAG Chatbot - Abdullah Akram

An **Agentic RAG** (Retrieval-Augmented Generation) chatbot that answers questions about Abdullah Akram using AI-powered tool calling, personal knowledge base search, web search, and GitHub stats.

**Live Demo:** [https://personal-rag-chatbot.vercel.app](https://personal-rag-chatbot.vercel.app)

---

## What Makes This Special?

This isn't a simple chatbot — it's an **agentic AI system** that autonomously decides which tools to use:

- **Ask about me** -> AI searches my personal knowledge base (ChromaDB vectors)
- **Ask general questions** -> AI searches the web (Tavily + DuckDuckGo)
- **Ask about my GitHub** -> AI fetches live data from GitHub API
- **Repeat questions** -> Instant responses from semantic cache

The LLM (Groq Llama 3.3 70B) acts as an intelligent agent that decides which tools to call, executes them, reasons over the results, and generates a comprehensive answer — all streamed in real-time.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | Groq Cloud (Llama 3.3 70B Versatile) — FREE |
| **Embeddings** | all-MiniLM-L6-v2 (local, 384 dimensions) — FREE |
| **Vector DB** | ChromaDB (local file, HNSW index) |
| **Web Search** | Tavily (primary) + DuckDuckGo (fallback) — FREE |
| **Backend** | FastAPI + Python 3.12 |
| **Frontend** | React 18 + Vite + Tailwind CSS |
| **MCP Server** | FastMCP (for Claude Desktop / Cursor) |
| **Backend Hosting** | HuggingFace Spaces (Docker) — FREE |
| **Frontend Hosting** | Vercel — FREE |

**Total Cost: $0/month**

---

## Features

- **Agentic Tool Calling** — LLM autonomously decides which tools to use (up to 3 rounds)
- **Real-time Streaming** — Server-Sent Events (SSE) for word-by-word responses
- **Tool Status Indicators** — Visual feedback showing which tool is being used
- **Semantic Cache** — 0.95 threshold for instant repeated answers (~350ms)
- **Conversation Memory** — 6-message context window per session
- **Graceful Fallback** — If tool calling fails, manual search + direct answer
- **MCP Integration** — Expose tools to Claude Desktop and Cursor IDE
- **Dark/Light Mode** — Toggle between themes
- **Mobile Responsive** — Works on all screen sizes
- **Rate Limiting** — 30 requests/minute per IP
- **45-second Timeout** — Prevents infinite loading

---

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Groq API key (free at console.groq.com)
- Tavily API key (free at tavily.com)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
GROQ_MODEL=llama-3.3-70b-versatile
GITHUB_USERNAME=your_github_username
EOF

# Ingest personal data into vector store
python ingest_data.py

# Start the server
python run.py
```

Server runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173 (proxies API to localhost:8000)

### MCP Server (Optional)

```bash
cd backend
python mcp_server.py
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | Health check |
| POST | /api/chat | Non-streaming chat |
| POST | /api/chat/stream | SSE streaming chat |

### Chat Request Body
```json
{
  "question": "What projects have you built?",
  "session_id": "optional-session-id"
}
```

---

## Architecture Overview

```
User Question
     |
     v
Semantic Cache (0.95 threshold)
     |
     +-- HIT --> Stream cached answer
     |
     +-- MISS --> Groq LLM + Tool Calling Loop (3 rounds max)
                       |
                       +-- search_personal_knowledge --> ChromaDB
                       +-- search_web --> Tavily / DuckDuckGo
                       +-- get_github_stats --> GitHub API
                       |
                       v
                  Stream Answer via SSE
                       |
                       v
               Cache + Store Conversation
```

> See [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) for detailed diagrams
> See [FLOW_DIAGRAM.md](FLOW_DIAGRAM.md) for micro-step flow diagrams

---

## Deployment

- **Backend**: HuggingFace Spaces (Docker) — [abdullah7570/personal-rag-chatbot](https://huggingface.co/spaces/abdullah7570/personal-rag-chatbot)
- **Frontend**: Vercel — auto-deploys from GitHub
- **Source**: GitHub — [iamabdullah1/personal-rag-llm-app](https://github.com/iamabdullah1/personal-rag-llm-app)

> See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions

---

## Project Documentation

| Document | Description |
|----------|-------------|
| [FLOW_DIAGRAM.md](FLOW_DIAGRAM.md) | Extensive micro-step flow diagrams |
| [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) | Complete system architecture |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment guide |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Implementation plan and status |
| [backend/COMPLETE_DOCUMENTATION.md](backend/COMPLETE_DOCUMENTATION.md) | Full backend documentation |

---

## License

This project is built as a personal portfolio piece by Abdullah Akram.

*Version 2.0.0 — Agentic Mode*
