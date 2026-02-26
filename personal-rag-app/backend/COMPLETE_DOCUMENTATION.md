# Complete Backend Documentation — Personal RAG Chatbot v2.0

> **Agentic RAG with Groq Tool Calling, MCP Server, and Intelligent Fallback**
> All features: 100% Complete

---

## Table of Contents

1. [Project Status](#project-status)
2. [Architecture Overview](#architecture-overview)
3. [File-by-File Documentation](#file-by-file-documentation)
4. [Tools System](#tools-system)
5. [Caching System](#caching-system)
6. [Conversation Memory](#conversation-memory)
7. [Error Handling and Fallback](#error-handling-and-fallback)
8. [Streaming System](#streaming-system)
9. [MCP Server](#mcp-server)
10. [Configuration](#configuration)
11. [Dependencies](#dependencies)

---

## Project Status

| Feature | Status | Notes |
|---------|--------|-------|
| FastAPI Backend | 100% | Lifespan pattern, middleware chain |
| Groq LLM Integration | 100% | Tool calling + streaming |
| ChromaDB Vector Store | 100% | Pre-ingested, HNSW index |
| Semantic Cache | 100% | 0.95 threshold, LRU, 7-day TTL |
| Conversation Memory | 100% | 10 msg limit, 24hr TTL, 6 to LLM |
| Web Search (Tavily) | 100% | Primary with DuckDuckGo fallback |
| GitHub Stats Tool | 100% | Profile + top 10 repos |
| Agentic Tool Calling | 100% | 3 rounds max, autonomous decisions |
| Fallback Pipeline | 100% | ToolCallError -> manual search -> direct answer |
| SSE Streaming | 100% | Token-by-token with tool status events |
| MCP Server | 100% | FastMCP, 3 tools exposed |
| Rate Limiting | 100% | 30 req/min per IP |
| Docker Deployment | 100% | HuggingFace Spaces |

**All features are fully implemented and deployed.**

---

## Architecture Overview

```
Request Flow:
  Client -> FastAPI -> Middleware -> Router -> RAG Service -> Groq + Tools -> SSE Response

Agentic Loop:
  Question -> Cache Check -> Groq (with tools) -> Tool Execution -> Groq (with results)
  -> More tools? -> Loop again (max 3) -> Final answer -> Stream -> Cache -> Store

Fallback:
  ToolCallError -> Manual vector search -> Manual web search -> Enriched prompt
  -> Groq (no tools) -> Stream -> User always gets an answer
```

---

## File-by-File Documentation

### app/main.py — Application Entry Point

**Version:** 2.0.0
**Pattern:** Lifespan context manager (replaced deprecated on_event)

**What it does:**
- Creates FastAPI app with lifespan manager
- Initializes RAG service on startup (loads ChromaDB, embeddings)
- Configures middleware chain: CORS -> Rate Limiter -> GZip -> Timing
- Mounts static files (built frontend) after API routes
- Rate limiter: 30 requests per minute per IP

**Middleware chain (order matters):**
1. CORS - Allows all origins (*)
2. Rate Limiter - Custom middleware, 30/min per IP, returns 429
3. GZip - Compresses responses > 500 bytes
4. Timing - Adds X-Process-Time header

### app/config.py — Settings

**Pattern:** Pydantic BaseSettings with .env file loading

**Key settings:**
- groq_api_key: Groq Cloud API key
- tavily_api_key: Tavily web search key
- groq_model: "llama-3.3-70b-versatile" (default)
- github_username: "iamabdullah1" (default)
- chunk_size: 1000, chunk_overlap: 200
- retriever_k: 3 (top K chunks to return)
- cache_threshold: 0.95
- max_conversations: 10 messages per session
- conversation_ttl: 86400 seconds (24 hours)

### app/routers/chat.py — API Endpoints

**Endpoints:**
- GET /api/health - Returns {"status": "healthy", "version": "2.0.0"}
- POST /api/chat - Non-streaming chat (JSON response)
- POST /api/chat/stream - SSE streaming chat

**Streaming format (SSE events):**
```
data: {"tool_status": "Searching personal knowledge base..."}
data: {"answer": "I've built "}
data: {"answer": "several "}
data: {"answer": "projects..."}
data: {"done": true, "session_id": "abc123"}
```

**Error handling:**
- On error: sends error event then done event
- Transfer-Encoding: chunked
- Cache-Control: no-cache

### app/services/rag_service.py — Agentic RAG Orchestrator

**This is the core of the application.** 528 lines.

**Key components:**

1. **TOOLS array** - 3 tool definitions in OpenAI function-calling format
   - search_personal_knowledge: Search personal docs
   - search_web: Search the internet
   - get_github_stats: Fetch GitHub profile

2. **RAGService class**
   - init(): Loads vectorstore + creates embedding function
   - _call_groq(): Sends messages to Groq with retry (3 attempts, exponential backoff)
   - _run_tool_loop(): Agentic loop - sends to Groq with tools, executes tools, loops up to 3 rounds
   - _fallback_answer(): When tool calling fails - manual vector search + web search + direct Groq call
   - stream_answer(): SSE generator - yields tool_status, answer chunks, done events
   - get_answer(): Non-streaming version

3. **ToolCallError** - Custom exception for tool calling failures

4. **Tool dispatch** - Maps function names to actual tool functions from tools.py

5. **Streaming flow:**
   - Check cache -> if hit, stream cached words
   - Build messages -> run tool loop -> get response
   - If ToolCallError -> fallback pipeline
   - Stream final response token-by-token
   - Cache Q&A pair -> store conversation

### app/services/tools.py — Shared Tool Functions

**3 async functions** used by both RAG service and MCP server:

1. **search_personal_knowledge(query)**
   - Searches ChromaDB vector store
   - Returns top 3 most similar document chunks
   - Uses the shared embedding function from vectorstore

2. **search_web(query)**
   - Primary: Tavily API (AI-optimized search results)
   - Fallback: DuckDuckGo (if Tavily fails or no API key)
   - Returns top 3 results as formatted text

3. **get_github_stats(username)**
   - Calls GitHub REST API (no auth needed for public data)
   - Returns profile info + top 10 repos (sorted by stars)
   - Uses httpx async client

### app/services/vectorstore.py — ChromaDB Setup

- Creates/loads ChromaDB persistent client at ./chroma_db/
- Uses HuggingFaceEmbeddings with all-MiniLM-L6-v2
- Provides get_retriever(k) for similarity search
- Collection name: "personal_docs"

### app/services/semantic_cache.py — Semantic Cache

- **Threshold**: 0.95 (cosine similarity)
- **Max entries**: 1000
- **TTL**: 7 days
- **Eviction**: LRU (Least Recently Used)
- Embeds questions using same all-MiniLM-L6-v2 model
- On cache hit: returns stored answer instantly (~50ms vs ~3s)
- Fixed from v1.0: threshold raised from 0.85 to prevent false matches

### app/services/conversation_store.py — Session History

- In-memory storage (per session_id)
- **Max messages**: 10 per session
- **TTL**: 24 hours (auto-cleanup)
- **Sent to LLM**: Last 6 messages (configurable)
- Auto-generates session_id if not provided

### mcp_server.py — MCP Server

- Uses FastMCP library
- Exposes 3 tools via Model Context Protocol
- Compatible with Claude Desktop, Cursor IDE
- Shares the same tool functions from tools.py
- Run: python mcp_server.py

### ingest_data.py — Data Ingestion

- Reads all .txt files from data/personal/
- Chunks using RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
- Embeds with all-MiniLM-L6-v2
- Stores in ChromaDB at ./chroma_db/
- Run: python ingest_data.py

### models/schemas.py — Pydantic Models

- ChatRequest: question (str), session_id (optional str)
- ChatResponse: answer (str), session_id (str), sources (list)

---

## Tools System

### How Tool Calling Works

1. User asks a question
2. RAG service sends question + 3 tool definitions to Groq
3. Groq returns either:
   - **Tool calls**: list of functions to execute with arguments
   - **Text content**: final answer (no tools needed)
4. If tool calls: execute each tool, append results, send back to Groq
5. Repeat up to 3 rounds

### Tool Definitions (OpenAI Format)

```
search_personal_knowledge:
  - Parameter: query (string) - Search query
  - Returns: Formatted text from top 3 ChromaDB chunks

search_web:
  - Parameter: query (string) - Search query
  - Returns: Formatted text from top 3 web results

get_github_stats:
  - Parameter: username (string) - GitHub username
  - Returns: Formatted profile info + top 10 repos
```

---

## Error Handling and Fallback

### ToolCallError

Raised when:
- Tool calling JSON parsing fails
- Tool execution throws an exception
- Groq returns unexpected format

### Fallback Pipeline

When ToolCallError is caught:
1. Manually search ChromaDB (vector search with top 3)
2. Manually search web (Tavily or DDG)
3. Build enriched prompt with gathered context
4. Call Groq WITHOUT tools (direct text generation)
5. User always receives an answer

This ensures 100% response rate even when tool calling has issues.

---

## Streaming System

### SSE Event Format

```
Event types:
  tool_status  -> {"tool_status": "Searching knowledge base..."}
  answer       -> {"answer": "partial text"}
  done         -> {"done": true, "session_id": "..."}
  error        -> {"error": "error message"}
```

### Stream Flow

1. Cache check -> if hit, split cached answer into words, yield with 0.03s delay
2. Tool loop -> yield tool_status events as tools execute
3. Final Groq streaming call -> yield answer tokens as they arrive
4. Post-stream: cache the Q&A, store conversation
5. Always end with done event

---

## Dependencies (requirements.txt)

Key packages:
- fastapi, uvicorn - Web framework
- groq - Groq Cloud SDK
- chromadb - Vector database
- sentence-transformers - Local embeddings
- langchain, langchain-community - Text splitting
- tavily-python - Web search
- duckduckgo-search - Fallback web search
- httpx - Async HTTP client (GitHub API)
- fastmcp - MCP server
- pydantic-settings - Configuration

---

*Complete Documentation v2.0 — Last Updated: June 2025*
