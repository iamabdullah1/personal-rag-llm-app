# 🏗️ Personal RAG Application — Complete Architecture Guide (v2.0)

> **Agentic RAG with Groq Tool Calling, MCP Server, and Intelligent Fallback**
> An AI-powered personal assistant that autonomously decides which tools to use.

**Last Updated:** June 2025
**Version:** 2.0.0 — Agentic Mode

---

## 📋 Table of Contents

1. [High-Level Overview](#high-level-overview)
2. [System Architecture Diagram](#system-architecture-diagram)
3. [Data Ingestion Pipeline](#data-ingestion-pipeline)
4. [Agentic Query Processing Flow](#agentic-query-processing-flow)
5. [Component Deep Dives](#component-deep-dives)
6. [Technology Stack](#technology-stack)
7. [Data Flow Examples](#data-flow-examples)
8. [File Structure](#file-structure)
9. [Performance Characteristics](#performance-characteristics)

---

## 🎯 High-Level Overview

### What Changed from v1.0 to v2.0?

| Aspect | v1.0 (Old) | v2.0 (Current) |
|--------|-----------|-----------------|
| **LLM** | HuggingFace Qwen 2.5 7B | Groq Llama 3.3 70B |
| **Architecture** | Simple RAG chain | Agentic tool-calling loop |
| **Web Search** | DuckDuckGo only | Tavily (primary) + DDG (fallback) |
| **Cache Threshold** | 0.85 (caused odd answers) | 0.95 (precise matching) |
| **Error Handling** | Basic try/catch | ToolCallError + fallback pipeline |
| **Streaming** | Broken/incomplete | Full SSE with tool status events |
| **MCP** | Not available | FastMCP server for Claude/Cursor |
| **Deployment** | Railway/Render | HuggingFace Spaces + Vercel |

### What is Agentic RAG?

**Agentic RAG** = The LLM autonomously decides WHAT tools to use and WHEN.

Unlike traditional RAG (retrieve then generate), Agentic RAG:
1. **Receives** the user's question
2. **Decides** which tools to call (personal knowledge, web search, GitHub)
3. **Executes** tools and receives results
4. **Reasons** over results — may call MORE tools if needed (up to 3 rounds)
5. **Generates** a final answer with all gathered context
6. **Falls back** gracefully if tool calling fails (user ALWAYS gets an answer)

---

## 🏛️ System Architecture Diagram

```
FRONTEND (React + Vite + Tailwind CSS) — Deployed on Vercel
==============================================================
  Chat Interface
  - User types question
  - Tool status indicators (Searching knowledge base / Searching web / Fetching GitHub)
  - SSE streaming (word by word)
  - 45-second timeout with AbortController
  - Dark/Light mode toggle
  - Mobile responsive
          |
          | POST /api/chat/stream (SSE)
          | Vercel rewrites -> HuggingFace Space
          v

BACKEND (FastAPI + Python 3.12) — Deployed on HuggingFace Spaces (Docker)
===========================================================================

  API Layer (Middleware Chain):
    CORS (*) -> Rate Limiter (30/min) -> GZip -> Timing Header
    Routes: /api/health | /api/chat | /api/chat/stream | /docs

          |
          v

  RAG Service (Agentic Orchestrator) — rag_service.py
  =====================================================
    Step 1: Check Semantic Cache (0.95 threshold)
            - HIT  -> Stream cached answer word-by-word -> DONE
            - MISS -> Continue to tool-calling loop

    Step 2: Build messages array
            [system_prompt] + [conversation_history (last 6)] + [user_question]

    Step 3: AGENTIC TOOL-CALLING LOOP (max 3 rounds)
            Send to Groq (llama-3.3-70b) with 3 tool definitions
              -> LLM decides: call tools? 
                 YES -> Execute tools -> Append results -> Next round
                 NO  -> Generate final answer -> Stream to user

    Step 4: If ToolCallError at any point -> FALLBACK MODE
            Manual vector search + web search -> enriched prompt -> Groq (no tools)

    Step 5: Stream answer via SSE -> Cache Q&A -> Store conversation -> done event

          |
          v

  3 Shared Tools — tools.py (used by RAG Service + MCP Server)
  ==============================================================
    search_personal_knowledge(query)  -> ChromaDB vector search (top 3 chunks)
    search_web(query)                 -> Tavily API (primary) / DuckDuckGo (fallback)
    get_github_stats(username)        -> GitHub REST API (profile + top 10 repos)

          |
          v

  Data Stores (all in-memory or local file)
  ==========================================
    Vector Store (ChromaDB)      -> ./chroma_db/ (HNSW index, all-MiniLM-L6-v2)
    Semantic Cache (In-Memory)   -> 0.95 threshold, 7-day TTL, 1000 max, LRU
    Conversation Store (In-Mem)  -> 10 msg limit per session, 24hr TTL

          |
          v

  MCP Server (Optional) — mcp_server.py
  =======================================
    FastMCP server exposing all 3 tools via Model Context Protocol
    For use with: Claude Desktop, Cursor IDE
    Run: python mcp_server.py

===========================================================================

EXTERNAL SERVICES (all free tier)
==================================
  Groq Cloud         -> LLM: Llama 3.3 70B, tool calling + streaming, FREE 14,400 req/day
  Tavily             -> Web search, FREE 1,000 searches/month, fallback: DuckDuckGo
  GitHub API         -> Public REST API, profile + repos, no auth needed
```

---

## 📥 Data Ingestion Pipeline

```
Step 1: LOAD
  - Read 9 text files from data/personal/
  - Files: about_me.txt, contact.txt, education.txt, hobbies_sports.txt,
           projects.txt, skills.txt, testimonials.txt, this_rag_project.txt,
           work_experience.txt

Step 2: CHUNK
  - RecursiveCharacterTextSplitter
  - Chunk size: 1000 characters
  - Overlap: 200 characters
  - Result: ~15-25 text chunks

Step 3: EMBED
  - Model: sentence-transformers/all-MiniLM-L6-v2
  - Runs locally on CPU (no API call, no cost)
  - Output: 384-dimensional vectors

Step 4: STORE
  - Database: ChromaDB (local file at ./chroma_db/)
  - Index: HNSW (Hierarchical Navigable Small World)
  - Ready for cosine similarity search

Run command: python ingest_data.py
```

---

## 🔍 Agentic Query Processing Flow

### Example: "What projects have you built using React?"

```
STAGE 1: CACHE CHECK
  - Embed query -> compare with cached questions
  - Similarity 0.82 < 0.95 threshold -> MISS -> continue

STAGE 2: BUILD MESSAGES
  - System prompt: "You are a helpful assistant for Abdullah Akram..."
  - History: [last 6 messages from session]
  - User: "What projects have you built using React?"

STAGE 3: GROQ CALL #1 (with tools)
  - Send messages + 3 tool definitions to Groq
  - LLM decides: call search_personal_knowledge("React projects built")
  - Response: tool_calls array with function name + arguments

STAGE 4: TOOL EXECUTION
  - Execute search_personal_knowledge("React projects built")
  - ChromaDB returns top 3 chunks from projects.txt and skills.txt
  - Append tool result to messages

STAGE 5: GROQ CALL #2 (with tool results)
  - LLM has enough context -> generates final answer (no more tool calls)
  - Response: streaming text content

STAGE 6: STREAM RESPONSE
  - Token by token via SSE
  - Frontend renders progressively
  - Events: tool_status -> answer chunks -> done

STAGE 7: POST-PROCESS
  - Cache the Q&A pair for future similar questions
  - Store in conversation history for session context
  - Send done event to frontend
```

> For extensive micro-step diagrams of every component, see **FLOW_DIAGRAM.md**

---

## 🔧 Component Deep Dives

### 1. LLM — Groq (Llama 3.3 70B Versatile)

| Feature | Details |
|---------|---------|
| **Provider** | Groq Cloud (console.groq.com) |
| **Model** | llama-3.3-70b-versatile |
| **Parameters** | 70 Billion |
| **Speed** | ~200 tokens/sec (Groq LPU hardware) |
| **Tool Calling** | Native OpenAI-compatible format |
| **Streaming** | Yes (SSE-compatible) |
| **Cost** | FREE (14,400 requests/day) |
| **Retry** | 3 attempts with exponential backoff (1s, 2s) |
| **Fallback** | On ToolCallError -> direct answer without tools |

### 2. Embedding Model (all-MiniLM-L6-v2)

| Feature | Details |
|---------|---------|
| **Type** | Sentence Transformer (BERT-based) |
| **Parameters** | 22.7 million |
| **Dimensions** | 384 |
| **Runs** | LOCALLY on CPU (no API, no cost, no latency) |
| **Speed** | ~14,000 sentences/sec |
| **Size** | ~80 MB |
| **Used For** | Vector search + Semantic cache similarity |

### 3. ChromaDB Vector Store

| Feature | Details |
|---------|---------|
| **Type** | Open-source embedding database |
| **Storage** | Local file (./chroma_db/) |
| **Index** | HNSW (Hierarchical Navigable Small World) |
| **Search** | Cosine similarity, O(log n) |
| **Returns** | Top 3 most similar chunks (retriever_k=3) |

### 4. Semantic Cache (0.95 Threshold)

| Feature | Details |
|---------|---------|
| **Threshold** | 0.95 (raised from 0.85 to fix false positive matches) |
| **Max Size** | 1000 Q&A pairs |
| **TTL** | 7 days |
| **Eviction** | LRU (Least Recently Used) |
| **Cache Hit Speed** | ~50ms (vs ~3s for full pipeline) |

### 5. Web Search — Tavily + DuckDuckGo

| Feature | Tavily (Primary) | DuckDuckGo (Fallback) |
|---------|-------------------|----------------------|
| **API Key** | Required (free tier) | Not needed |
| **Free Tier** | 1,000 searches/month | Unlimited (may rate limit) |
| **Quality** | AI-optimized results | Standard results |
| **Reliability** | High | Can be blocked in production |
| **Max Results** | 3 | 3 |

### 6. MCP Server

| Feature | Details |
|---------|---------|
| **Protocol** | Model Context Protocol (by Anthropic) |
| **Library** | FastMCP |
| **Tools Exposed** | search_knowledge, search_web, get_github_stats |
| **Clients** | Claude Desktop, Cursor IDE |
| **Run** | python mcp_server.py |

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18, Vite, Tailwind CSS | Chat UI with streaming |
| **Backend** | FastAPI, Uvicorn, Pydantic | REST API + SSE streaming |
| **LLM** | Groq Cloud (Llama 3.3 70B) | Tool calling + text generation |
| **Embeddings** | all-MiniLM-L6-v2 (local) | Text to 384-dim vectors |
| **Vector DB** | ChromaDB | Similarity search |
| **Web Search** | Tavily + DuckDuckGo | External knowledge |
| **MCP** | FastMCP | Tool exposure for AI clients |
| **Caching** | In-memory (cosine similarity) | Fast repeat responses |
| **Deployment** | HuggingFace Spaces + Vercel | Backend + Frontend hosting |
| **Source Code** | GitHub | Version control |

**Total monthly cost: $0.00** (all free tiers)

---

## 📊 Data Flow Examples

### Personal Question (Vector Search)
```
"What programming languages do you know?"
  -> Groq decides: search_personal_knowledge("programming languages")
  -> ChromaDB returns: skills.txt chunks (0.94, 0.88, 0.82 similarity)
  -> Groq generates: "I'm proficient in JavaScript, Python, TypeScript..."
```

### General Knowledge (Web Search)
```
"What is machine learning?"
  -> Groq decides: search_web("what is machine learning")
  -> Tavily returns: 3 web results with summaries
  -> Groq generates: "Machine learning is a branch of AI that..."
```

### GitHub Stats (API)
```
"Show me your GitHub repos"
  -> Groq decides: get_github_stats("iamabdullah1")
  -> GitHub API returns: profile info + top 10 repos
  -> Groq generates: "I have 15 public repos, including..."
```

### Cache Hit (Instant)
```
"What are your skills?" (repeated question)
  -> Semantic Cache: similarity 0.97 >= 0.95 threshold -> HIT
  -> Stream cached answer word-by-word (~350ms total)
```

### Fallback (Graceful Degradation)
```
"Tell me about your work" (tool calling fails)
  -> Groq tool call -> ToolCallError (JSON parse failure)
  -> Fallback: manual vector search + manual web search
  -> Enriched prompt -> Groq (no tools, direct answer)
  -> User still gets a helpful response
```

---

## 📁 File Structure

```
personal-rag-app/
  Root Documentation:
    FLOW_DIAGRAM.md              -- Extensive micro-step flow diagrams (14 sections)
    PROJECT_ARCHITECTURE.md      -- This file (system architecture guide)
    IMPLEMENTATION_PLAN.md       -- Implementation plan and completion status
    DEPLOYMENT.md                -- Deployment guide (HF Spaces + Vercel)
    README.md                    -- Project overview and quick start
    Dockerfile                   -- Root Docker configuration

  backend/
    app/
      main.py                    -- FastAPI app, lifespan manager, middleware (v2.0.0)
      config.py                  -- Settings: Groq, Tavily, GitHub, RAG parameters
      routers/
        chat.py                  -- API endpoints: /health, /chat, /chat/stream
      services/
        rag_service.py           -- Agentic RAG orchestrator (Groq tool calling loop)
        tools.py                 -- 3 shared tools (knowledge, web, GitHub)
        vectorstore.py           -- ChromaDB + HuggingFace embeddings setup
        semantic_cache.py        -- 0.95 threshold semantic cache (LRU, 7-day TTL)
        conversation_store.py    -- In-memory session history (10 msg, 24hr TTL)
      models/
        schemas.py               -- Pydantic request/response models
    data/personal/               -- 9 personal text documents
    chroma_db/                   -- Pre-ingested vector database
    static/                      -- Built frontend files (served by FastAPI)
    mcp_server.py                -- MCP server for Claude Desktop / Cursor
    ingest_data.py               -- Data ingestion script
    requirements.txt             -- Python dependencies
    Dockerfile                   -- Backend Docker configuration
    .env                         -- API keys (gitignored)

  frontend/
    src/
      App.jsx                    -- React chat component (SSE, tools, timeout, dark mode)
      main.jsx                   -- React entry point
      App.css                    -- Component styles
      index.css                  -- Global styles (Tailwind)
    vite.config.js               -- Dev proxy to localhost:8000
    vercel.json                  -- Production proxy to HF Space
    tailwind.config.js           -- Tailwind CSS configuration
    package.json                 -- Node.js dependencies
    index.html                   -- HTML entry point
```

---

## 📈 Performance Characteristics

| Scenario | Response Time | Groq API Calls | Tools Used | Cost |
|----------|--------------|----------------|------------|------|
| Cache Hit | ~350ms | 0 | 0 | $0 |
| Single Tool (personal) | ~2-3s | 2 | 1 | $0 |
| Single Tool (web) | ~2-3s | 2 | 1 | $0 |
| Multi-Tool | ~3-4s | 2-3 | 2+ | $0 |
| Fallback Mode | ~6-8s | 3-4 | manual | $0 |

### Rate Limits

| Service | Free Tier Limit | Daily/Monthly |
|---------|-----------------|---------------|
| Groq | 14,400 requests | Per day |
| Tavily | 1,000 searches | Per month |
| GitHub API | 60 requests | Per hour (unauthenticated) |
| Backend Rate Limiter | 30 requests | Per minute per IP |

---

## 🔐 Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| GROQ_API_KEY | Groq Cloud LLM access | Yes |
| TAVILY_API_KEY | Tavily web search | Yes |
| GROQ_MODEL | LLM model name | No (default: llama-3.3-70b-versatile) |
| GITHUB_USERNAME | GitHub stats tool | No (default: iamabdullah1) |

---

**Created for Abdullah Akram's Personal RAG Portfolio Application**

*Architecture Document v2.0 — Agentic Mode*
