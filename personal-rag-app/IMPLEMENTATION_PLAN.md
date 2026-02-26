# 🛠️ Implementation Plan — Personal RAG App Fix + MCP Integration

**Date:** February 25, 2026  
**Status:** ✅ ALL PHASES COMPLETED — Deployed and Live  
**Goal:** Fix all bugs (infinite loading, odd answers) + integrate MCP server for agentic RAG

---

## Phase 1 — Bug Fixes ✅ COMPLETED

| # | Bug | Root Cause | Fix |
|---|-----|-----------|-----|
| 1 | **Infinite loading** | HuggingFace router is slow/unreliable, zero retry logic, 60s timeout with no fallback | Switch to **Groq** (free tier, fast) + add retry logic |
| 2 | **Loading never stops on error** | Frontend: if streaming ends without `data.done`, `setLoading(false)` never gets called | Add reader-completion guard + 45s timeout |
| 3 | **Odd/wrong answers** | Semantic cache threshold too low (0.85) — different questions return cached wrong answers | Raise threshold to **0.95** for exact match |
| 4 | **Duplicate conversation storage** | `stream_llm_response` saves AND `get_answer_streaming` may double-save | Consolidate save logic — save only once in final step |
| 5 | **DuckDuckGo blocked in prod** | `duckduckgo_search` gets rate-limited on HuggingFace Spaces | Replace with **Tavily** (free tier, reliable) + DuckDuckGo fallback |
| 6 | **No frontend request timeout** | If backend hangs, frontend waits forever | Add `AbortController` 45s timeout |
| 7 | **Deprecated FastAPI events** | `@app.on_event("startup")` deprecated | Replace with `lifespan` context manager |
| 8 | **f-string bug in semantic_cache** | Nested quotes in f-string print statement (line ~138) | Fix string formatting |

---

## Phase 2 — MCP Tool Integration (Agentic RAG) ✅ COMPLETED

| # | Task | File(s) | Detail |
|---|------|---------|--------|
| 1 | **Create shared tools** | `backend/app/services/tools.py` | 3 async tools: `search_personal_knowledge`, `search_web`, `get_github_stats` |
| 2 | **Rewrite RAG service** | `backend/app/services/rag_service.py` | Groq SDK + tool-calling loop. LLM decides which tools to call. Multi-round support. |
| 3 | **Create MCP server** | `backend/mcp_server.py` | MCP server exposing all 3 tools for Claude Desktop / Cursor integration |
| 4 | **Update config** | `backend/.env`, `backend/app/config.py` | Add `GROQ_API_KEY`, `TAVILY_API_KEY`, `GITHUB_USERNAME`, `GROQ_MODEL` |
| 5 | **Simplify chat router** | `backend/app/routers/chat.py` | Use new `stream_answer()` generator, cleaner error handling |
| 6 | **Frontend improvements** | `frontend/src/App.jsx` | Timeout, error recovery, tool-usage status indicator |

---

## Phase 3 — Deployment & Testing ✅ COMPLETED

| # | Task |
|---|------|
| 1 | Update `requirements.txt` with `groq`, `tavily-python`, `mcp` |
| 2 | Install packages and test locally |
| 3 | Verify streaming works end-to-end |
| 4 | Document env vars needed in HuggingFace Spaces secrets |

---

## Architecture (New)

```
User Message
     ↓
FastAPI Backend (/api/chat/stream)
     ↓
Groq LLM (with tool definitions)
     ↓
LLM decides: "Do I need tools?"
     │
     ├── search_personal_knowledge → ChromaDB → results → LLM
     ├── search_web → Tavily/DuckDuckGo → results → LLM
     ├── get_github_stats → GitHub API → results → LLM
     └── No tools needed → direct answer
     ↓
Streaming answer → SSE → Frontend
```

---

## API Keys Required

| Key | Source | Purpose |
|-----|--------|---------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | LLM (Llama 3.3 70B) |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) | Web search |
| `HUGGINGFACE_API_KEY` | existing | Embeddings — NOTE: runs locally, no API key needed |
| `GITHUB_USERNAME` | config | GitHub stats tool |

---

## Files Changed

### New Files
- `IMPLEMENTATION_PLAN.md` — this file
- `backend/app/services/tools.py` — shared tool implementations
- `backend/mcp_server.py` — MCP server for external clients

### Modified Files
- `backend/.env` — new API keys
- `backend/app/config.py` — new settings
- `backend/app/services/rag_service.py` — **complete rewrite** (Groq + tool calling)
- `backend/app/services/semantic_cache.py` — threshold fix + f-string fix
- `backend/app/main.py` — lifespan fix
- `backend/app/routers/chat.py` — simplified streaming
- `frontend/src/App.jsx` — infinite loading fix + timeout + error handling
- `backend/requirements.txt` — new packages

---

## ✅ Completion Summary

**All phases completed and deployed successfully.**

- Backend: Live on HuggingFace Spaces (Docker)
- Frontend: Live on Vercel
- All 8 bugs fixed
- Agentic tool calling working
- MCP server ready
- Streaming + fallback working
- Total cost: $0/month

*Plan completed — June 2025*
