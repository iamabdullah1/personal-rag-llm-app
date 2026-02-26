# Personal RAG Chatbot — Backend

FastAPI backend for the Agentic RAG chatbot with Groq tool calling, ChromaDB vector store, and MCP server integration.

**Version:** 2.0.0 — Agentic Mode

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI + Uvicorn |
| **LLM** | Groq Cloud (Llama 3.3 70B) |
| **Embeddings** | all-MiniLM-L6-v2 (local) |
| **Vector DB** | ChromaDB |
| **Web Search** | Tavily (primary) + DuckDuckGo (fallback) |
| **MCP** | FastMCP |
| **Python** | 3.12 |

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Ingest personal data
python ingest_data.py

# Run the server
python run.py
```

Server: http://localhost:8000
API Docs: http://localhost:8000/docs

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/health | Health check (returns version) |
| POST | /api/chat | Non-streaming chat response |
| POST | /api/chat/stream | SSE streaming chat response |

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| GROQ_API_KEY | Groq Cloud API key | Required |
| TAVILY_API_KEY | Tavily web search key | Required |
| GROQ_MODEL | LLM model name | llama-3.3-70b-versatile |
| GITHUB_USERNAME | For GitHub stats tool | iamabdullah1 |

## Architecture

The backend uses an **agentic architecture** where the LLM decides which tools to call:

1. Check semantic cache (0.95 threshold)
2. Build message history (system + last 6 messages + question)
3. Groq tool-calling loop (up to 3 rounds)
4. Stream response via SSE
5. Cache answer + store conversation

See [PROJECT_ARCHITECTURE.md](../PROJECT_ARCHITECTURE.md) and [FLOW_DIAGRAM.md](../FLOW_DIAGRAM.md) for detailed diagrams.
