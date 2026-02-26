# 🔄 Complete Flow Diagrams — Personal RAG Application v2.0 (Agentic)

> **Every micro-step of the entire system explained through visual flow diagrams.**
> From the moment a user types a message to the final streamed token — nothing is hidden.

**Last Updated:** February 26, 2026
**Version:** 2.0.0 — Agentic RAG with Groq Tool Calling

---

## 📋 Table of Contents

1. [End-to-End Master Flow](#1-end-to-end-master-flow)
2. [Frontend Request Flow (Micro Steps)](#2-frontend-request-flow-micro-steps)
3. [Backend API Processing Flow](#3-backend-api-processing-flow)
4. [Agentic Tool-Calling Loop (The Brain)](#4-agentic-tool-calling-loop-the-brain)
5. [Tool Execution Flows](#5-tool-execution-flows)
   - [5a. search_personal_knowledge](#5a-search_personal_knowledge-tool)
   - [5b. search_web](#5b-search_web-tool)
   - [5c. get_github_stats](#5c-get_github_stats-tool)
6. [Fallback Mechanism Flow](#6-fallback-mechanism-flow)
7. [Streaming Response Flow (SSE)](#7-streaming-response-flow-sse)
8. [Semantic Cache Flow](#8-semantic-cache-flow)
9. [Conversation Memory Flow](#9-conversation-memory-flow)
10. [Data Ingestion Pipeline](#10-data-ingestion-pipeline)
11. [MCP Server Flow (External Clients)](#11-mcp-server-flow-external-clients)
12. [Deployment Architecture](#12-deployment-architecture)
13. [Error Handling & Recovery Matrix](#13-error-handling--recovery-matrix)
14. [Complete Example Walkthroughs](#14-complete-example-walkthroughs)

---

## 1. End-to-End Master Flow

### The Complete Journey of a Single User Message

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          🌐 USER TYPES MESSAGE IN BROWSER                                │
│                     "What projects have you built using React?"                           │
└───────────────────────────────────────┬─────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──── STEP 1: FRONTEND ────────────────────────────────────────────────────────────────────┐
│                                                                                           │
│  1.1  User clicks Send / presses Enter                                                   │
│  1.2  React state: setLoading(true), add user msg to messages[]                          │
│  1.3  Create AbortController with 45-second timeout                                      │
│  1.4  POST /api/chat/stream  { message, session_id }                                    │
│  1.5  Read SSE stream line by line                                                       │
│                                                                                           │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        │  HTTPS (Vercel → HuggingFace Space)
                                        ▼
┌──── STEP 2: FASTAPI BACKEND ─────────────────────────────────────────────────────────────┐
│                                                                                           │
│  2.1  Request hits CORS middleware → passes (allow_origins: *)                           │
│  2.2  Rate limiter checks IP → 30 req/min → passes                                      │
│  2.3  Timing middleware starts timer                                                     │
│  2.4  Router /api/chat/stream receives request                                           │
│  2.5  Calls rag_service.stream_answer(question, session_id)                              │
│                                                                                           │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──── STEP 3: RAG SERVICE ─────────────────────────────────────────────────────────────────┐
│                                                                                           │
│  3.1  Generate session_id if none provided (uuid4)                                       │
│  3.2  ─── SEMANTIC CACHE CHECK ───                                                       │
│       3.2a  Convert question → embedding vector (384 dims)                               │
│       3.2b  Compare with all cached Q&A embeddings (cosine similarity)                   │
│       3.2c  If similarity ≥ 0.95 → CACHE HIT → stream cached answer → DONE              │
│       3.2d  If similarity < 0.95 → CACHE MISS → continue                                │
│  3.3  Retrieve last 6 messages from conversation store                                   │
│  3.4  Build message array: [system_prompt] + [history] + [user_question]                 │
│                                                                                           │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──── STEP 4: AGENTIC TOOL-CALLING LOOP ───────────────────────────────────────────────────┐
│                                                                                           │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐    │
│  │  ROUND 1 (of max 3):                                                              │    │
│  │                                                                                    │    │
│  │  4.1  Send messages + 3 tool definitions to Groq API (non-streaming)              │    │
│  │       Model: llama-3.3-70b-versatile                                               │    │
│  │       tool_choice: "auto"                                                          │    │
│  │                                                                                    │    │
│  │  4.2  Groq LLM analyzes the question and decides:                                 │    │
│  │                                                                                    │    │
│  │       ┌────────────────────────────────────────────────────────────────────────┐  │    │
│  │       │  DECISION TREE (inside the LLM's "brain"):                              │  │    │
│  │       │                                                                         │  │    │
│  │       │  Q: "What projects have you built using React?"                         │  │    │
│  │       │      ↓                                                                  │  │    │
│  │       │  Is this about the person? → YES                                        │  │    │
│  │       │      ↓                                                                  │  │    │
│  │       │  Tool: search_personal_knowledge("React projects built")                │  │    │
│  │       │                                                                         │  │    │
│  │       │  ─── OR ───                                                             │  │    │
│  │       │                                                                         │  │    │
│  │       │  Q: "What is machine learning?"                                         │  │    │
│  │       │      ↓                                                                  │  │    │
│  │       │  Is this about the person? → NO, it's general knowledge                 │  │    │
│  │       │      ↓                                                                  │  │    │
│  │       │  Tool: search_web("what is machine learning")                           │  │    │
│  │       │                                                                         │  │    │
│  │       │  ─── OR ───                                                             │  │    │
│  │       │                                                                         │  │    │
│  │       │  Q: "Show me your GitHub repos"                                         │  │    │
│  │       │      ↓                                                                  │  │    │
│  │       │  Tool: get_github_stats("iamabdullah1")                                 │  │    │
│  │       │                                                                         │  │    │
│  │       │  ─── OR ───                                                             │  │    │
│  │       │                                                                         │  │    │
│  │       │  Q: "Hello!" / simple greeting                                          │  │    │
│  │       │      ↓                                                                  │  │    │
│  │       │  No tools needed → answer directly                                      │  │    │
│  │       └────────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                                    │    │
│  │  4.3  If LLM chose tools:                                                         │    │
│  │       4.3a  Parse tool_calls from response                                        │    │
│  │       4.3b  Yield { tool_call: "search_personal_knowledge" } → frontend shows 🔍  │    │
│  │       4.3c  Execute tool async → get JSON result                                  │    │
│  │       4.3d  Append tool result to messages[]                                      │    │
│  │       4.3e  → Next round (LLM sees results + can call more tools)                │    │
│  │                                                                                    │    │
│  │  4.4  If LLM answered directly (no tools):                                        │    │
│  │       → Stream answer word-by-word → DONE                                         │    │
│  │                                                                                    │    │
│  └──────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                           │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐    │
│  │  ROUND 2-3 (if needed):                                                           │    │
│  │  Same process — LLM can call additional tools based on previous results           │    │
│  │  Example: After personal search, LLM might also call search_web for context       │    │
│  └──────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                           │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐    │
│  │  ⚠️  IF TOOL CALLING FAILS (ToolCallError):                                       │    │
│  │  4.5  Catch ToolCallError exception                                               │    │
│  │  4.6  → FALLBACK MODE (see Section 6)                                             │    │
│  └──────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                           │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──── STEP 5: STREAMING PHASE ─────────────────────────────────────────────────────────────┐
│                                                                                           │
│  5.1  Call Groq API again with all messages (including tool results) — STREAMING mode    │
│  5.2  For each chunk from Groq:                                                          │
│       5.2a  Extract delta.content (a few characters at a time)                           │
│       5.2b  Yield { token: "..." }                                                       │
│       5.2c  Append to full_answer buffer                                                 │
│  5.3  After stream ends:                                                                 │
│       5.3a  Save to conversation store (user msg + assistant msg)                        │
│       5.3b  Cache Q&A pair in semantic cache                                             │
│       5.3c  Yield { done: true, sources: [...], session_id: "..." }                      │
│                                                                                           │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──── STEP 6: RESPONSE DELIVERY ───────────────────────────────────────────────────────────┐
│                                                                                           │
│  6.1  FastAPI StreamingResponse sends SSE events to frontend                             │
│  6.2  Frontend reads each SSE line:                                                      │
│       6.2a  { tool_call: "..." } → show tool status indicator (🔍 🌐 🐙)               │
│       6.2b  { token: "..." }     → append to message display (typing effect)            │
│       6.2c  { done: true }       → setLoading(false), clear timeout                     │
│       6.2d  { error: "..." }     → show error message                                   │
│  6.3  Message fully rendered in chat UI                                                  │
│                                                                                           │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Frontend Request Flow (Micro Steps)

### What happens inside React when the user sends a message

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                     FRONTEND: App.jsx — sendMessage() Flow                                │
└──────────────────────────────────────────────────────────────────────────────────────────┘

USER ACTION: Types "What skills do you have?" → clicks Send
                │
                ▼
┌─── Step 2.1: INPUT VALIDATION ──────────────────────────────────────────────────────────┐
│                                                                                          │
│  if (!input.trim() || loading) return;       // Reject empty / duplicate clicks         │
│  const userMessage = input.trim();                                                       │
│  setInput('');                                // Clear input box immediately             │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 2.2: OPTIMISTIC UI UPDATE ──────────────────────────────────────────────────────┐
│                                                                                          │
│  setMessages(prev => [...prev, { role: 'user', content: userMessage }]);                │
│  setMessages(prev => [...prev, { role: 'assistant', content: '' }]);                    │
│  setLoading(true);                                                                       │
│  setToolStatus(null);                                                                    │
│                                                                                          │
│  RESULT: User sees their message + empty assistant bubble immediately                   │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 2.3: TIMEOUT SETUP ─────────────────────────────────────────────────────────────┐
│                                                                                          │
│  const controller = new AbortController();                                              │
│  timeoutRef.current = setTimeout(() => {                                                │
│      controller.abort();                   // Kill request after 45 seconds             │
│  }, 45000);                                                                              │
│                                                                                          │
│  PURPOSE: Prevents infinite loading if backend hangs                                    │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 2.4: FETCH REQUEST ─────────────────────────────────────────────────────────────┐
│                                                                                          │
│  const response = await fetch('/api/chat/stream', {                                     │
│      method: 'POST',                                                                    │
│      headers: { 'Content-Type': 'application/json' },                                  │
│      body: JSON.stringify({                                                              │
│          message: userMessage,                                                           │
│          session_id: conversationId                                                     │
│      }),                                                                                 │
│      signal: controller.signal                                                           │
│  });                                                                                     │
│                                                                                          │
│  ROUTING (Production):                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Browser (Vercel)                                                                   │ │
│  │    → /api/chat/stream                                                               │ │
│  │    → vercel.json rewrite                                                            │ │
│  │    → https://abdullah7570-personal-rag-chatbot.hf.space/api/chat/stream             │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  ROUTING (Development):                                                                 │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Browser (localhost:3000)                                                           │ │
│  │    → /api/chat/stream                                                               │ │
│  │    → vite.config.js proxy                                                           │ │
│  │    → http://localhost:8000/api/chat/stream                                          │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 2.5: STREAM READING LOOP ───────────────────────────────────────────────────────┐
│                                                                                          │
│  const reader = response.body.getReader();                                              │
│  const decoder = new TextDecoder();                                                     │
│  let streamDone = false;                                                                 │
│                                                                                          │
│  while (true) {                                                                          │
│      const { done, value } = await reader.read();                                       │
│      if (done) break;                                                                    │
│                                                                                          │
│      const text = decoder.decode(value, { stream: true });                              │
│      const lines = text.split('\n');                                                    │
│                                                                                          │
│      for (const line of lines) {                                                        │
│          if (!line.startsWith('data: ')) continue;                                      │
│          const data = JSON.parse(line.slice(6));                                        │
│                                                                                          │
│          ┌──────────────────────────────────────────────────────────────────────────┐   │
│          │  EVENT HANDLING:                                                          │   │
│          │                                                                           │   │
│          │  if (data.tool_call) {                                                    │   │
│          │      setToolStatus(data.tool_call);                                       │   │
│          │      // Shows: 🔍 Searching knowledge base...                             │   │
│          │      //        🌐 Searching the web...                                    │   │
│          │      //        🐙 Checking GitHub...                                      │   │
│          │      //        🔧 Processing...                                           │   │
│          │  }                                                                        │   │
│          │                                                                           │   │
│          │  if (data.token) {                                                        │   │
│          │      setToolStatus(null);                                                 │   │
│          │      // Append token to last message's content                            │   │
│          │      setMessages(prev => {                                                │   │
│          │          const updated = [...prev];                                       │   │
│          │          updated[updated.length - 1].content += data.token;               │   │
│          │      });                                                                  │   │
│          │  }                                                                        │   │
│          │                                                                           │   │
│          │  if (data.done) {                                                         │   │
│          │      streamDone = true;                                                   │   │
│          │      setConversationId(data.session_id);                                  │   │
│          │  }                                                                        │   │
│          │                                                                           │   │
│          │  if (data.error) {                                                        │   │
│          │      // Display error in message bubble                                   │   │
│          │  }                                                                        │   │
│          └──────────────────────────────────────────────────────────────────────────┘   │
│      }                                                                                   │
│  }                                                                                       │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 2.6: STREAM FINALIZATION GUARD ─────────────────────────────────────────────────┐
│                                                                                          │
│  // If stream ended but we never got { done: true }                                     │
│  if (!streamDone && messages[last].content) {                                           │
│      // Message already has content → display it anyway                                 │
│  }                                                                                       │
│                                                                                          │
│  // Always clean up:                                                                    │
│  clearTimeout(timeoutRef.current);                                                      │
│  setLoading(false);                                                                      │
│  setToolStatus(null);                                                                    │
│                                                                                          │
│  PURPOSE: Prevents infinite loading even if { done } event is lost                      │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Backend API Processing Flow

### Inside FastAPI: From HTTP request to RAG service

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                     BACKEND: chat.py Router — /api/chat/stream                            │
└──────────────────────────────────────────────────────────────────────────────────────────┘

HTTP POST /api/chat/stream arrives
    Body: { "message": "What skills do you have?", "session_id": "abc-123" }
                │
                ▼
┌─── Step 3.1: MIDDLEWARE CHAIN ──────────────────────────────────────────────────────────┐
│                                                                                          │
│  ① GZip Middleware                                                                      │
│     → Compresses responses > 500 bytes                                                  │
│                                                                                          │
│  ② CORS Middleware                                                                      │
│     → Adds Access-Control-Allow-Origin: *                                               │
│     → Passes OPTIONS preflight requests                                                 │
│                                                                                          │
│  ③ Rate Limiter Middleware                                                              │
│     → Extract client IP from request.client.host                                        │
│     → Clean old entries (> 60 seconds ago)                                              │
│     → Count requests in last minute                                                     │
│     → If count ≥ 30 → Return 429 "Too many requests"                                   │
│     → If count < 30 → Add timestamp → Pass through                                     │
│                                                                                          │
│  ④ Timing Middleware                                                                    │
│     → Record start_time = time.time()                                                   │
│     → (After response) Add X-Process-Time header                                       │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 3.2: ROUTE HANDLER ─────────────────────────────────────────────────────────────┐
│                                                                                          │
│  @router.post("/chat/stream")                                                           │
│  async def chat_stream(request: ChatRequest):                                           │
│                                                                                          │
│  3.2a  Validate request via Pydantic ChatRequest schema                                 │
│        ├── message: str (required, non-empty)                                           │
│        └── session_id: str (optional)                                                   │
│                                                                                          │
│  3.2b  Log incoming request                                                             │
│        logger.info(f"Stream: '{question[:60]}' session={session_id}")                   │
│                                                                                          │
│  3.2c  Create async generator wrapper around rag_service.stream_answer()                │
│                                                                                          │
│  3.2d  Return StreamingResponse(                                                        │
│            generate(),                                                                   │
│            media_type="text/event-stream",                                              │
│            headers={                                                                     │
│                "Cache-Control": "no-cache",                                             │
│                "X-Accel-Buffering": "no",                                               │
│                "Transfer-Encoding": "chunked"                                           │
│            }                                                                             │
│        )                                                                                 │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 3.3: SSE GENERATOR ─────────────────────────────────────────────────────────────┐
│                                                                                          │
│  async def generate():                                                                  │
│      try:                                                                                │
│          async for event in rag_service.stream_answer(question, session_id):            │
│              yield f"data: {json.dumps(event)}\n\n"                                     │
│      except Exception as e:                                                              │
│          yield f"data: {json.dumps({'error': str(e)})}\n\n"                             │
│          yield f"data: {json.dumps({'done': True})}\n\n"   # Always send done!          │
│                                                                                          │
│  FORMAT of each SSE line:                                                               │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  data: {"tool_call": "search_personal_knowledge"}\n\n                              │ │
│  │  data: {"token": "I "}\n\n                                                         │ │
│  │  data: {"token": "have "}\n\n                                                      │ │
│  │  data: {"token": "skills "}\n\n                                                    │ │
│  │  data: {"token": "in..."}\n\n                                                      │ │
│  │  data: {"done": true, "sources": [...], "session_id": "abc-123"}\n\n               │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Agentic Tool-Calling Loop (The Brain)

### The core decision engine — how the LLM decides what tools to use

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   AGENTIC TOOL-CALLING LOOP — _run_tool_loop()                            │
│                                                                                           │
│   This is what makes this system "agentic" — the LLM autonomously decides                │
│   WHAT tools to call, WHEN to call them, and HOW to combine results.                     │
└──────────────────────────────────────────────────────────────────────────────────────────┘

INPUT: messages = [system_prompt, ...history, user_question]
                │
                ▼
┌─── ROUND 1 OF 3 ────────────────────────────────────────────────────────────────────────┐
│                                                                                          │
│  4.1  API CALL TO GROQ                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  POST https://api.groq.com/openai/v1/chat/completions                              │ │
│  │                                                                                     │ │
│  │  {                                                                                  │ │
│  │    "model": "llama-3.3-70b-versatile",                                              │ │
│  │    "messages": [ ...messages ],                                                     │ │
│  │    "tools": [                                                                       │ │
│  │      {                                                                              │ │
│  │        "type": "function",                                                          │ │
│  │        "function": {                                                                │ │
│  │          "name": "search_personal_knowledge",                                       │ │
│  │          "description": "Search personal knowledge base...",                        │ │
│  │          "parameters": { "type": "object", "properties": { "query": {...} } }      │ │
│  │        }                                                                            │ │
│  │      },                                                                             │ │
│  │      { "function": { "name": "search_web", ... } },                                │ │
│  │      { "function": { "name": "get_github_stats", ... } }                           │ │
│  │    ],                                                                               │ │
│  │    "tool_choice": "auto",                                                           │ │
│  │    "max_tokens": 800,                                                               │ │
│  │    "temperature": 0.7,                                                              │ │
│  │    "stream": false                                                                  │ │
│  │  }                                                                                  │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  4.2  GROQ RESPONSE ANALYSIS                                                            │
│                                                                                          │
│  response.choices[0].message =                                                          │
│                                                                                          │
│  ┌──── CASE A: LLM CHOSE TOOLS ────────────────────────────────────────────────────┐   │
│  │  {                                                                                │   │
│  │    "role": "assistant",                                                           │   │
│  │    "tool_calls": [                                                                │   │
│  │      {                                                                            │   │
│  │        "id": "call_abc123",                                                       │   │
│  │        "type": "function",                                                        │   │
│  │        "function": {                                                              │   │
│  │          "name": "search_personal_knowledge",                                     │   │
│  │          "arguments": "{\"query\": \"React projects skills\"}"                    │   │
│  │        }                                                                          │   │
│  │      }                                                                            │   │
│  │    ]                                                                              │   │
│  │  }                                                                                │   │
│  │                                                                                   │   │
│  │  → Execute tool (see Section 5)                                                   │   │
│  │  → Append assistant message + tool result to messages[]                           │   │
│  │  → Continue to Round 2                                                            │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│  ┌──── CASE B: LLM ANSWERED DIRECTLY ──────────────────────────────────────────────┐   │
│  │  {                                                                                │   │
│  │    "role": "assistant",                                                           │   │
│  │    "content": "Hi! I'm Abdullah Akram, nice to meet you!"                        │   │
│  │  }                                                                                │   │
│  │                                                                                   │   │
│  │  → Return answer immediately                                                     │   │
│  │  → No tools needed (e.g., simple greetings)                                      │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│  ┌──── CASE C: TOOL CALL FORMAT ERROR ─────────────────────────────────────────────┐   │
│  │                                                                                   │   │
│  │  Groq returns: "tool_use_failed" error                                           │   │
│  │  (Llama 3.3 sometimes generates malformed tool calls)                            │   │
│  │                                                                                   │   │
│  │  → Retry with exponential backoff (1s, 2s)                                       │   │
│  │  → After max retries → Raise ToolCallError                                       │   │
│  │  → Caller catches → Switches to FALLBACK MODE (Section 6)                        │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │ (If tool was called)
                                   ▼
┌─── ROUND 2 OF 3 (if needed) ────────────────────────────────────────────────────────────┐
│                                                                                          │
│  Messages now include:                                                                  │
│  [system, ...history, user_question, assistant_tool_call, tool_result]                  │
│                                                                                          │
│  4.3  Send updated messages to Groq                                                     │
│                                                                                          │
│  LLM sees the tool results and decides:                                                 │
│  ├── "I have enough info" → Generate final answer → DONE                               │
│  ├── "I need more info"   → Call another tool → Round 3                                 │
│  └── "Let me combine"     → Call different tool for context → Round 3                   │
│                                                                                          │
│  Example: After getting personal knowledge, LLM might also                              │
│           call search_web("React latest features") for context                          │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── ROUND 3 OF 3 (max) ──────────────────────────────────────────────────────────────────┐
│                                                                                          │
│  Final round — if still calling tools after 3 rounds:                                   │
│  → Call Groq WITHOUT tools (force a text answer)                                        │
│  → Return whatever the LLM generates                                                    │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘


TOOL-CALLING MESSAGE CHAIN EXAMPLE (What Groq sees):
═══════════════════════════════════════════════════

Message #1: { role: "system",    content: "You ARE the person..." }
Message #2: { role: "user",      content: "What are your skills?" }     ← Previous turn
Message #3: { role: "assistant", content: "I specialize in..." }        ← Previous turn
Message #4: { role: "user",      content: "What React projects did you build?" }  ← Current
Message #5: { role: "assistant", tool_calls: [{name: "search_personal_knowledge"}] }
Message #6: { role: "tool",      content: '{"results": [...]}' }        ← Tool output
Message #7: { role: "assistant", content: "I've built several React..." }  ← Final answer
```

---

## 5. Tool Execution Flows

### 5a. search_personal_knowledge Tool

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   TOOL: search_personal_knowledge(query)                                  │
│                   File: backend/app/services/tools.py                                    │
└──────────────────────────────────────────────────────────────────────────────────────────┘

INPUT: query = "React projects built"
                │
                ▼
┌─── Step 5a.1: GET RETRIEVER ────────────────────────────────────────────────────────────┐
│                                                                                          │
│  from app.services.vectorstore import vectorstore_service                               │
│  retriever = vectorstore_service.get_retriever()                                        │
│                                                                                          │
│  Retriever config:                                                                      │
│  ├── search_type: "similarity"                                                          │
│  ├── k: 3 (return top 3 chunks)                                                        │
│  └── distance_metric: cosine similarity                                                 │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 5a.2: EMBEDDING GENERATION ─────────────────────────────────────────────────────┐
│                                                                                          │
│  Model: sentence-transformers/all-MiniLM-L6-v2 (runs LOCALLY)                           │
│                                                                                          │
│  "React projects built"                                                                  │
│       │                                                                                  │
│       ▼                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  Tokenizer: ["react", "projects", "built"]                                      │    │
│  │       │                                                                          │    │
│  │       ▼                                                                          │    │
│  │  6 Transformer Layers (BERT-based)                                               │    │
│  │       │                                                                          │    │
│  │       ▼                                                                          │    │
│  │  Mean Pooling                                                                    │    │
│  │       │                                                                          │    │
│  │       ▼                                                                          │    │
│  │  [0.234, -0.567, 0.891, 0.034, ... , -0.445]  (384 dimensions)                 │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                          │
│  Time: ~20ms (CPU)                                                                      │
│  Cost: $0 (runs locally)                                                                │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 5a.3: CHROMADB SIMILARITY SEARCH ───────────────────────────────────────────────┐
│                                                                                          │
│  ChromaDB uses HNSW (Hierarchical Navigable Small World) index                          │
│                                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                    VECTOR SPACE VISUALIZATION                                       │ │
│  │                                                                                     │ │
│  │                     Query ●                                                         │ │
│  │                          ╲  0.93                                                    │ │
│  │                           ● projects.txt (chunk 1) "Built RAG app with React..."   │ │
│  │                                                                                     │ │
│  │                    ● skills.txt (chunk 2) "React, Node.js..." [0.88]               │ │
│  │                                                                                     │ │
│  │             ● projects.txt (chunk 2) "E-Commerce platform..." [0.82]               │ │
│  │                                                                                     │ │
│  │        ● about_me.txt "Full-Stack Developer..." [0.71]                             │ │
│  │                                                                                     │ │
│  │   ● education.txt "Bachelor in Computer Science" [0.45]                            │ │
│  │                                                                                     │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  Returns top 3: projects.txt(0.93), skills.txt(0.88), projects.txt(0.82)               │
│  Time: ~50ms                                                                            │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 5a.4: FORMAT RESULTS ───────────────────────────────────────────────────────────┐
│                                                                                          │
│  OUTPUT:                                                                                │
│  {                                                                                       │
│    "results": [                                                                          │
│      { "content": "Built RAG app with React, FastAPI...", "source": "projects.txt" },   │
│      { "content": "Skills: React, Node.js, Python...", "source": "skills.txt" },        │
│      { "content": "E-Commerce Platform with React...", "source": "projects.txt" }       │
│    ],                                                                                    │
│    "count": 3                                                                            │
│  }                                                                                       │
│                                                                                          │
│  This JSON is sent back to the LLM as a tool result message                            │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5b. search_web Tool

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   TOOL: search_web(query)                                                 │
│                   File: backend/app/services/tools.py                                    │
└──────────────────────────────────────────────────────────────────────────────────────────┘

INPUT: query = "What is machine learning"
                │
                ▼
┌─── Step 5b.1: TRY TAVILY (Primary) ────────────────────────────────────────────────────┐
│                                                                                          │
│  if settings.tavily_api_key exists and is valid:                                        │
│                                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  TavilyClient(api_key=TAVILY_API_KEY)                                              │ │
│  │  response = client.search(query, max_results=3)                                    │ │
│  │                                                                                     │ │
│  │  Tavily is designed for AI agents — returns clean, relevant results                │ │
│  │  FREE tier: 1,000 searches/month                                                   │ │
│  │                                                                                     │ │
│  │  If successful → Return results → DONE                                             │ │
│  │  If error → Fall through to DuckDuckGo                                             │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │ (If Tavily fails or unavailable)
                                   ▼
┌─── Step 5b.2: TRY DUCKDUCKGO (Fallback) ───────────────────────────────────────────────┐
│                                                                                          │
│  from duckduckgo_search import DDGS                                                     │
│  ddgs = DDGS()                                                                          │
│  results = ddgs.text(query, max_results=3)                                              │
│                                                                                          │
│  DuckDuckGo: FREE, no API key, but can be rate-limited in production                   │
│                                                                                          │
│  If successful → Return results → DONE                                                  │
│  If error → Return empty results with error message                                     │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 5b.3: FORMAT RESULTS ───────────────────────────────────────────────────────────┐
│                                                                                          │
│  OUTPUT:                                                                                │
│  {                                                                                       │
│    "results": [                                                                          │
│      {                                                                                   │
│        "title": "Machine Learning - Wikipedia",                                         │
│        "content": "Machine learning is a subset of AI that enables...",                 │
│        "url": "https://en.wikipedia.org/wiki/Machine_learning"                          │
│      },                                                                                  │
│      { ... },                                                                            │
│      { ... }                                                                             │
│    ],                                                                                    │
│    "count": 3,                                                                           │
│    "source": "tavily"  // or "duckduckgo"                                               │
│  }                                                                                       │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5c. get_github_stats Tool

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   TOOL: get_github_stats(username)                                        │
│                   File: backend/app/services/tools.py                                    │
└──────────────────────────────────────────────────────────────────────────────────────────┘

INPUT: username = "iamabdullah1" (default from config)
                │
                ▼
┌─── Step 5c.1: FETCH USER PROFILE ───────────────────────────────────────────────────────┐
│                                                                                          │
│  GET https://api.github.com/users/iamabdullah1                                          │
│  Headers: Accept: application/vnd.github.v3+json                                        │
│  Timeout: 10 seconds                                                                    │
│                                                                                          │
│  Returns: name, bio, public_repos, followers, following, html_url                       │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 5c.2: FETCH REPOSITORIES ───────────────────────────────────────────────────────┐
│                                                                                          │
│  GET https://api.github.com/users/iamabdullah1/repos                                    │
│      ?sort=updated&per_page=10&direction=desc                                           │
│                                                                                          │
│  Returns: Top 10 repos sorted by last updated                                           │
│  Fields: name, description, language, stars, forks, url, updated_at                     │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 5c.3: FORMAT RESULTS ───────────────────────────────────────────────────────────┐
│                                                                                          │
│  OUTPUT:                                                                                │
│  {                                                                                       │
│    "profile": {                                                                          │
│      "name": "Abdullah Akram",                                                          │
│      "bio": "...",                                                                       │
│      "public_repos": 15,                                                                │
│      "followers": 10,                                                                    │
│      "url": "https://github.com/iamabdullah1"                                          │
│    },                                                                                    │
│    "recent_repos": [                                                                     │
│      { "name": "personal-rag-llm-app", "language": "Python", "stars": 2 },             │
│      { ... }                                                                             │
│    ]                                                                                     │
│  }                                                                                       │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Fallback Mechanism Flow

### What happens when Groq's tool calling breaks

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   FALLBACK MECHANISM — _fallback_answer()                                  │
│                                                                                           │
│   WHY: Llama 3.3 on Groq sometimes generates malformed tool call JSON.                   │
│   Groq returns "tool_use_failed" error. Without fallback = user gets nothing.            │
│   With fallback = user ALWAYS gets an answer.                                             │
└──────────────────────────────────────────────────────────────────────────────────────────┘

TRIGGER: ToolCallError raised after max retries (2 retries = 3 total attempts)
                │
                ▼
┌─── Step 6.1: MANUAL PERSONAL SEARCH ────────────────────────────────────────────────────┐
│                                                                                          │
│  try:                                                                                    │
│      personal_result = await search_personal_knowledge(question)                        │
│      personal_context = join all result contents                                        │
│  except:                                                                                 │
│      personal_context = ""  (fail silently)                                             │
│                                                                                          │
│  PURPOSE: Gather personal knowledge even without LLM tool calling                       │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 6.2: MANUAL WEB SEARCH ─────────────────────────────────────────────────────────┐
│                                                                                          │
│  try:                                                                                    │
│      web_result = await search_web(question)                                            │
│      web_context = format results as bullet points                                      │
│  except:                                                                                 │
│      web_context = ""  (fail silently)                                                  │
│                                                                                          │
│  PURPOSE: Gather web knowledge even without LLM tool calling                            │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 6.3: BUILD ENRICHED PROMPT ─────────────────────────────────────────────────────┐
│                                                                                          │
│  enriched_question = f"""                                                               │
│  PERSONAL CONTEXT:                                                                      │
│  {personal_context}                                                                      │
│                                                                                          │
│  WEB SEARCH RESULTS:                                                                    │
│  {web_context}                                                                           │
│                                                                                          │
│  Question: {original_question}                                                          │
│  """                                                                                     │
│                                                                                          │
│  This manually does what tool calling would have done — BUT without                     │
│  relying on the LLM to format tool calls correctly.                                     │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 6.4: CALL GROQ WITHOUT TOOLS ───────────────────────────────────────────────────┐
│                                                                                          │
│  messages = [system_prompt, ...history, enriched_question]                               │
│  response = await _call_groq(messages, tools=None, stream=False)                        │
│                              ──────────────                                              │
│                              NO tools passed!                                            │
│                                                                                          │
│  LLM generates answer from the manually-gathered context                                │
│  → No tool calling needed → No format errors possible                                   │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 6.5: RETURN ANSWER ─────────────────────────────────────────────────────────────┐
│                                                                                          │
│  return (answer, sources)                                                               │
│                                                                                          │
│  The user gets a complete, high-quality answer — they never know                        │
│  that the tool calling failed. Seamless degradation.                                    │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘


RETRY FLOW DETAIL:
═════════════════

    Attempt 1 → Groq API call with tools
                │
                ├── Success → Return response
                │
                └── "tool_use_failed" → Wait 1 second
                                          │
                                          ▼
    Attempt 2 → Groq API call with tools
                │
                ├── Success → Return response
                │
                └── "tool_use_failed" → Wait 2 seconds
                                          │
                                          ▼
    Attempt 3 → Groq API call with tools
                │
                ├── Success → Return response
                │
                └── "tool_use_failed" → RAISE ToolCallError
                                          │
                                          ▼
                            Caught by caller → _fallback_answer()
                                          │
                                          ▼
                            User gets answer (100% of the time)
```

---

## 7. Streaming Response Flow (SSE)

### How tokens flow from Groq → FastAPI → Browser in real-time

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   SERVER-SENT EVENTS (SSE) STREAMING PIPELINE                             │
└──────────────────────────────────────────────────────────────────────────────────────────┘

Phase 1: Tool Status Events (non-streaming)
═══════════════════════════════════════════

  Groq (non-streaming) → RAG Service → FastAPI → Frontend
                                │
                                │ yield {"tool_call": "search_personal_knowledge"}
                                │
                                ▼
  Browser receives: data: {"tool_call": "search_personal_knowledge"}\n\n
       │
       ▼
  UI shows: 🔍 Searching knowledge base...


Phase 2: Token Streaming (real-time)
═══════════════════════════════════

  Groq API (streaming=True) → RAG Service → FastAPI → Frontend

  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │                                                                                      │
  │  GROQ                  RAG SERVICE            FASTAPI              BROWSER           │
  │  ─────                 ───────────            ───────              ───────           │
  │                                                                                      │
  │  chunk: "I"        →   yield {"token":"I "}  → data: {"token":"I "}\n\n  → "I "     │
  │  chunk: " have"    →   yield {"token":" have"} → data: {"token":" have"}\n\n  → "I have" │
  │  chunk: " built"   →   yield {"token":" built"} → ...                     → "I have built" │
  │  chunk: " several" →   yield {"token":" several"} → ...                   → "I have built several" │
  │  chunk: " React"   →   yield {"token":" React"} → ...                    → "I have built several React" │
  │  chunk: " projects" →  yield {"token":" projects"} → ...                 → (full text) │
  │  ...               →   ...                    → ...                       → ...       │
  │  [stream ends]     →   yield {"done": true,   → data: {"done": true,     → setLoading │
  │                    →    sources: [...],        →  sources: [...],          →  (false)   │
  │                    →    session_id: "..."  }   →  session_id: "..."}\n\n  →            │
  │                                                                                      │
  └─────────────────────────────────────────────────────────────────────────────────────┘

  Total latency per token: < 50ms (Groq is very fast)
  User perception: Real-time typing effect


Phase 3: Cache Hit Streaming (simulated)
════════════════════════════════════════

  When cache hit: No Groq API call. Answer already in memory.

  Cached answer: "I specialize in React, Node.js, Python..."
       │
       ▼
  Split into words: ["I", "specialize", "in", "React,", "Node.js,", "Python..."]
       │
       ▼
  for word in words:
      yield {"token": word + " "}
      await asyncio.sleep(0.02)   # 20ms delay = simulated typing effect
       │
       ▼
  yield {"done": true, sources: ["Semantic Cache"], session_id: "..."}

  Result: Looks the same to user, but response starts in <50ms (vs 2-3s)
```

---

## 8. Semantic Cache Flow

### Two-level caching system with 0.95 threshold

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   SEMANTIC CACHE — semantic_cache.py                                      │
│                                                                                           │
│   Config:                                                                                │
│   ├── similarity_threshold: 0.95 (must be 95% similar for exact match)                  │
│   ├── max_cache_size: 1000 Q&A pairs                                                    │
│   ├── ttl_hours: 168 (7 days)                                                            │
│   └── eviction_policy: LRU (Least Recently Used)                                        │
└──────────────────────────────────────────────────────────────────────────────────────────┘

WRITE PATH (After every new answer):
═══════════════════════════════════

  semantic_cache.add(question, answer)
       │
       ▼
  ┌─── Step 1: Generate Embedding ─────────────────────────────────┐
  │  question_embedding = model.encode(question)                   │
  │  → [0.23, -0.45, 0.87, ...]  (384 dims)                      │
  └───────────────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
  ┌─── Step 2: Create Cache Entry ─────────────────────────────────┐
  │  entry = {                                                     │
  │      "question": "What projects have you built?",              │
  │      "answer": "I've built several projects including...",     │
  │      "embedding": [0.23, -0.45, ...],                         │
  │      "timestamp": 1740000000,                                  │
  │      "hit_count": 0                                            │
  │  }                                                             │
  └───────────────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
  ┌─── Step 3: Check Size Limit ───────────────────────────────────┐
  │  if len(cache) >= 1000:                                        │
  │      evict oldest/least-used entry (LRU)                       │
  │  cache.append(entry)                                           │
  └────────────────────────────────────────────────────────────────┘


READ PATH (Before every query):
══════════════════════════════

  semantic_cache.get_exact_match(question)
       │
       ▼
  ┌─── Step 1: Generate Embedding ─────────────────────────────────┐
  │  query_embedding = model.encode(question)                      │
  └───────────────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
  ┌─── Step 2: Compare with All Cache Entries ─────────────────────┐
  │                                                                │
  │  for each cached_entry:                                        │
  │      similarity = cosine_similarity(query_emb, cached_emb)     │
  │                                                                │
  │  ┌──────────────────────────────────────────────────────────┐ │
  │  │  Query: "What projects have you worked on?"               │ │
  │  │                                                           │ │
  │  │  Cached: "What projects have you built?"                  │ │
  │  │  Similarity: 0.96 ≥ 0.95 → ✅ EXACT MATCH               │ │
  │  │                                                           │ │
  │  │  Cached: "What are your skills?"                          │ │
  │  │  Similarity: 0.52 < 0.95 → ❌ No match                   │ │
  │  │                                                           │ │
  │  │  Cached: "Tell me about your education"                   │ │
  │  │  Similarity: 0.38 < 0.95 → ❌ No match                   │ │
  │  └──────────────────────────────────────────────────────────┘ │
  │                                                                │
  │  Best match: 0.96 → Return cached answer                      │
  └───────────────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
  ┌─── Step 3: Return Result ──────────────────────────────────────┐
  │                                                                │
  │  IF similarity ≥ 0.95:                                         │
  │      → Increment hit_count                                     │
  │      → Return cached answer string                             │
  │      → Skip entire RAG pipeline ⚡ (~50ms vs ~3s)             │
  │                                                                │
  │  IF similarity < 0.95:                                         │
  │      → Return None                                             │
  │      → Continue to full RAG pipeline                           │
  │                                                                │
  └────────────────────────────────────────────────────────────────┘


WHY 0.95 AND NOT 0.85?
══════════════════════

  Old threshold (0.85):
  ┌───────────────────────────────────────────────────────┐
  │  Q: "What are your hobbies?"          (cached)        │
  │  Q: "What are your skills?"           (new question)  │
  │  Similarity: 0.87 ≥ 0.85 → FALSE MATCH ❌            │
  │  Result: Returns hobbies answer for skills question!  │
  │  User sees: WRONG/ODD ANSWER (original bug)          │
  └───────────────────────────────────────────────────────┘

  New threshold (0.95):
  ┌───────────────────────────────────────────────────────┐
  │  Q: "What are your hobbies?"          (cached)        │
  │  Q: "What are your skills?"           (new question)  │
  │  Similarity: 0.87 < 0.95 → CORRECTLY REJECTED ✅     │
  │  Result: Full RAG pipeline runs → correct answer      │
  │                                                        │
  │  Q: "What have you built?"            (cached)        │
  │  Q: "What projects have you built?"   (new question)  │
  │  Similarity: 0.96 ≥ 0.95 → CORRECTLY MATCHED ✅      │
  │  Result: Returns cached answer (same meaning)         │
  └───────────────────────────────────────────────────────┘
```

---

## 9. Conversation Memory Flow

### How the chatbot remembers previous messages

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   CONVERSATION STORE — conversation_store.py                               │
│                                                                                           │
│   Storage: In-memory dictionary  { session_id → [messages] }                             │
│   Limit: 10 messages per session                                                         │
│   TTL: 24 hours                                                                           │
│   Context window: Last 6 messages sent to LLM                                            │
└──────────────────────────────────────────────────────────────────────────────────────────┘


WRITE PATH:
══════════

  conversation_store.add_message(session_id, role, content)
       │
       ▼
  ┌─── Step 1: Get or Create Session ──────────────────────────────┐
  │  if session_id not in store:                                   │
  │      store[session_id] = {                                     │
  │          "messages": [],                                       │
  │          "created_at": now,                                    │
  │          "last_active": now                                    │
  │      }                                                         │
  └───────────────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
  ┌─── Step 2: Append Message ─────────────────────────────────────┐
  │  store[session_id]["messages"].append({                        │
  │      "role": "user" / "assistant",                             │
  │      "content": "..."                                          │
  │  })                                                            │
  │  store[session_id]["last_active"] = now                        │
  └───────────────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
  ┌─── Step 3: Enforce Limit ──────────────────────────────────────┐
  │  if len(messages) > 10:                                        │
  │      messages = messages[-10:]   # Keep only last 10          │
  └────────────────────────────────────────────────────────────────┘


READ PATH:
═════════

  conversation_store.get_history_for_llm(session_id)
       │
       ▼
  ┌─── Step 1: Get Messages ───────────────────────────────────────┐
  │  messages = store.get(session_id, {}).get("messages", [])      │
  └───────────────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
  ┌─── Step 2: Return Last 6 ─────────────────────────────────────┐
  │  return messages[-6:]   # Only last 6 messages for context    │
  │                                                                │
  │  WHY 6? Balance between context and token usage:              │
  │  • Too few (2-4): Loses conversation context                  │
  │  • Too many (10+): Wastes tokens, slower, may confuse LLM    │
  │  • 6 (3 turns): Good balance for follow-up questions          │
  └────────────────────────────────────────────────────────────────┘


EXAMPLE CONVERSATION FLOW:
═════════════════════════

  Turn 1:
  ┌─────────────────────────────────────────────────────────────────┐
  │  User: "What companies have you worked for?"                   │
  │  Store: [user_msg]                                             │
  │  LLM sees: [system, user_msg]                                 │
  │  Answer: "I worked at Meldin, Apexez, and now freelancing"     │
  │  Store: [user_msg, assistant_msg]                              │
  └─────────────────────────────────────────────────────────────────┘

  Turn 2:
  ┌─────────────────────────────────────────────────────────────────┐
  │  User: "Tell me more about the first one"                      │
  │  Store: [user_1, asst_1, user_2]                              │
  │  LLM sees: [system, user_1, asst_1, user_2]                  │
  │  → LLM knows "first one" = Meldin (from conversation history) │
  │  Answer: "At Meldin, I worked on..."                          │
  │  Store: [user_1, asst_1, user_2, asst_2]                     │
  └─────────────────────────────────────────────────────────────────┘

  Turn 3:
  ┌─────────────────────────────────────────────────────────────────┐
  │  User: "What tech did you use there?"                          │
  │  Store: [user_1, asst_1, user_2, asst_2, user_3]             │
  │  LLM sees: [system, user_1, asst_1, user_2, asst_2, user_3]  │
  │  → LLM knows "there" = Meldin (from full context)             │
  │  Answer: "At Meldin, I used React, Node.js..."                │
  └─────────────────────────────────────────────────────────────────┘
```

---

## 10. Data Ingestion Pipeline

### How personal documents become searchable vectors

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   DATA INGESTION — ingest_data.py                                         │
│                   Run: python ingest_data.py                                              │
└──────────────────────────────────────────────────────────────────────────────────────────┘

┌─── Step 10.1: LOAD RAW DOCUMENTS ───────────────────────────────────────────────────────┐
│                                                                                          │
│  📁 data/personal/                                                                      │
│  ├── about_me.txt              (~500 chars)                                             │
│  ├── contact.txt               (~200 chars)                                             │
│  ├── education.txt             (~800 chars)                                             │
│  ├── hobbies_sports.txt        (~600 chars)                                             │
│  ├── projects.txt              (~2000 chars)                                            │
│  ├── skills.txt                (~1200 chars)                                            │
│  ├── testimonials.txt          (~1000 chars)                                            │
│  ├── this_rag_project.txt      (~1500 chars)                                            │
│  └── work_experience.txt       (~1800 chars)                                            │
│                                                                                          │
│  Loader: LangChain DirectoryLoader + TextLoader                                        │
│  Result: 9 raw Document objects                                                         │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 10.2: SPLIT INTO CHUNKS ────────────────────────────────────────────────────────┐
│                                                                                          │
│  RecursiveCharacterTextSplitter:                                                        │
│  ├── chunk_size: 1000 characters                                                        │
│  ├── chunk_overlap: 200 characters                                                      │
│  └── separators: ["\n\n", "\n", " ", ""]                                                │
│                                                                                          │
│  BEFORE:  1 document = 2000 chars                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐                │
│  │ ████████████████████████████████████████████████████████████████████ │                │
│  └─────────────────────────────────────────────────────────────────────┘                │
│                                                                                          │
│  AFTER:   3 chunks with 200-char overlap                                                │
│  ┌───────────────────────────┐                                                          │
│  │ Chunk 1 (chars 0–1000)    │                                                          │
│  └───────────────────┬───────┘                                                          │
│              ┌───────┴───────────────────┐                                               │
│              │ Chunk 2 (chars 800–1800)   │                                               │
│              └───────────────────┬───────┘                                               │
│                          ┌───────┴───────────────┐                                       │
│                          │ Chunk 3 (chars 1600–2000) │                                    │
│                          └───────────────────────┘                                       │
│                                                                                          │
│  Total: ~15-25 chunks from 9 documents                                                  │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 10.3: GENERATE EMBEDDINGS ──────────────────────────────────────────────────────┐
│                                                                                          │
│  Model: sentence-transformers/all-MiniLM-L6-v2                                          │
│  Runs: LOCALLY (no API, no cost)                                                        │
│                                                                                          │
│  For each chunk:                                                                        │
│      text → Tokenize → 6 Transformer Layers → Mean Pool → 384-dim vector              │
│                                                                                          │
│  Time: ~2 seconds for all chunks (CPU)                                                  │
│                                                                                          │
└──────────────────────────────────┬───────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─── Step 10.4: STORE IN CHROMADB ────────────────────────────────────────────────────────┐
│                                                                                          │
│  ChromaDB.from_documents(chunks, embeddings, persist_directory="./chroma_db")           │
│                                                                                          │
│  Stored per chunk:                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐                 │
│  │  ID:        "chunk_001"                                           │                 │
│  │  Text:      "I'm Abdullah Akram, a Full-Stack Developer..."      │                 │
│  │  Vector:    [0.023, -0.156, 0.891, ...]  (384 dims)             │                 │
│  │  Metadata:  { source: "data/personal/about_me.txt" }            │                 │
│  └────────────────────────────────────────────────────────────────────┘                 │
│                                                                                          │
│  Files created:                                                                         │
│  ./chroma_db/                                                                           │
│  ├── chroma.sqlite3                    (metadata & config)                              │
│  └── e355630e-39fc-.../                (collection)                                     │
│      ├── data_level0.bin               (vectors)                                        │
│      ├── header.bin                    (HNSW index header)                              │
│      ├── length.bin                    (data lengths)                                   │
│      └── link_lists.bin               (HNSW graph structure)                           │
│                                                                                          │
│  ✅ Ready for similarity search!                                                        │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. MCP Server Flow (External Clients)

### How Claude Desktop / Cursor connects to your tools via MCP

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   MCP SERVER — mcp_server.py                                              │
│                   Protocol: Model Context Protocol (by Anthropic)                         │
│                   Run: python mcp_server.py                                               │
└──────────────────────────────────────────────────────────────────────────────────────────┘

ARCHITECTURE:
════════════

  ┌───────────────────────────┐
  │   Claude Desktop          │
  │   or Cursor IDE           │
  │   (MCP Client)            │
  └─────────┬─────────────────┘
            │ MCP Protocol (stdio / SSE)
            ▼
  ┌───────────────────────────┐
  │   mcp_server.py           │
  │   (FastMCP Server)        │
  │                           │
  │   Exposes 3 tools:        │
  │   ├── search_knowledge    │
  │   ├── search_web          │
  │   └── get_github_stats    │
  └─────────┬─────────────────┘
            │ Calls shared tool functions
            ▼
  ┌───────────────────────────┐
  │   tools.py                │
  │   (Shared implementations)│
  │                           │
  │   Same functions used by  │
  │   both FastAPI backend    │
  │   AND MCP server          │
  └───────────────────────────┘


MCP REQUEST FLOW:
════════════════

  Claude Desktop User: "What projects has Abdullah built?"
       │
       ▼
  ┌─── Step 1: Claude sees available tools ────────────────────────┐
  │  Tools registered via FastMCP:                                 │
  │  ├── search_knowledge(query: str) → str                       │
  │  ├── search_web(query: str) → str                             │
  │  └── get_github_stats(username: str) → str                    │
  └───────────────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
  ┌─── Step 2: Claude decides to call tool ────────────────────────┐
  │  Claude: "I'll search the knowledge base"                      │
  │  → Calls search_knowledge("Abdullah projects")                │
  └───────────────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
  ┌─── Step 3: MCP server executes ────────────────────────────────┐
  │  mcp_server.py receives request                                │
  │  → Calls search_personal_knowledge("Abdullah projects")       │
  │  → ChromaDB similarity search                                  │
  │  → Returns JSON results                                        │
  └───────────────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
  ┌─── Step 4: Claude generates answer ────────────────────────────┐
  │  Claude receives tool results                                  │
  │  → Generates natural language answer                           │
  │  → Displays in Claude Desktop UI                               │
  └────────────────────────────────────────────────────────────────┘


CLAUDE DESKTOP CONFIGURATION:
════════════════════════════

  File: ~/Library/Application Support/Claude/claude_desktop_config.json

  {
    "mcpServers": {
      "personal-rag": {
        "command": "python",
        "args": ["/path/to/backend/mcp_server.py"],
        "env": {
          "GROQ_API_KEY": "...",
          "TAVILY_API_KEY": "..."
        }
      }
    }
  }
```

---

## 12. Deployment Architecture

### Production infrastructure: HuggingFace Spaces + Vercel

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   PRODUCTION DEPLOYMENT ARCHITECTURE                                      │
└──────────────────────────────────────────────────────────────────────────────────────────┘


  ┌─── USER'S BROWSER ────────────────────────────────────────────────────────────────────┐
  │                                                                                        │
  │  https://personal-rag-app.vercel.app                                                  │
  │  (React SPA served by Vercel CDN)                                                     │
  │                                                                                        │
  └────────────────────────────────────┬───────────────────────────────────────────────────┘
                                       │
                                       │ /api/* requests
                                       ▼
  ┌─── VERCEL (Frontend Host) ─────────────────────────────────────────────────────────────┐
  │                                                                                        │
  │  vercel.json rewrites:                                                                │
  │  {                                                                                     │
  │    "rewrites": [                                                                       │
  │      {                                                                                 │
  │        "source": "/api/:path*",                                                       │
  │        "destination": "https://abdullah7570-personal-rag-chatbot.hf.space/api/:path*"  │
  │      }                                                                                 │
  │    ]                                                                                   │
  │  }                                                                                     │
  │                                                                                        │
  │  Static files (HTML, CSS, JS) served from Vercel Edge Network                         │
  │  API calls proxied to HuggingFace Space                                               │
  │                                                                                        │
  └────────────────────────────────────┬───────────────────────────────────────────────────┘
                                       │
                                       │ HTTPS proxy
                                       ▼
  ┌─── HUGGINGFACE SPACES (Backend Host) ──────────────────────────────────────────────────┐
  │                                                                                        │
  │  Space: abdullah7570/personal-rag-chatbot                                             │
  │  Runtime: Docker                                                                       │
  │  URL: https://abdullah7570-personal-rag-chatbot.hf.space                              │
  │                                                                                        │
  │  ┌─── Docker Container ───────────────────────────────────────────────────────────┐   │
  │  │                                                                                 │   │
  │  │  Base: python:3.12-slim                                                        │   │
  │  │                                                                                 │   │
  │  │  ┌─── FastAPI Application ──────────────────────────────────────────────────┐  │   │
  │  │  │  Port: 7860 (HF Spaces default)                                          │  │   │
  │  │  │  Workers: 1 (Uvicorn)                                                    │  │   │
  │  │  │                                                                          │  │   │
  │  │  │  ┌── Routes ──────────────────────────────────────────────────────────┐  │  │   │
  │  │  │  │  GET  /api/health      → Health check                              │  │  │   │
  │  │  │  │  POST /api/chat        → Non-streaming chat                        │  │  │   │
  │  │  │  │  POST /api/chat/stream → SSE streaming chat                        │  │  │   │
  │  │  │  │  GET  /docs            → Swagger UI                                │  │  │   │
  │  │  │  │  GET  /*               → Static files (backup frontend)            │  │  │   │
  │  │  │  └────────────────────────────────────────────────────────────────────┘  │  │   │
  │  │  │                                                                          │  │   │
  │  │  │  ┌── Services ────────────────────────────────────────────────────────┐  │  │   │
  │  │  │  │  RAG Service     → Groq + tool calling + fallback                  │  │  │   │
  │  │  │  │  Vector Store    → ChromaDB (local file)                           │  │  │   │
  │  │  │  │  Semantic Cache  → In-memory (resets on redeploy)                  │  │  │   │
  │  │  │  │  Conv. Store     → In-memory (resets on redeploy)                  │  │  │   │
  │  │  │  └────────────────────────────────────────────────────────────────────┘  │  │   │
  │  │  └──────────────────────────────────────────────────────────────────────────┘  │   │
  │  │                                                                                 │   │
  │  │  ┌── Data ──────────────────────────────────────────────────────────────────┐  │   │
  │  │  │  /app/chroma_db/        (pre-ingested vectors)                           │  │   │
  │  │  │  /app/data/personal/    (source .txt files)                              │  │   │
  │  │  │  /app/static/           (built frontend)                                 │  │   │
  │  │  └──────────────────────────────────────────────────────────────────────────┘  │   │
  │  │                                                                                 │   │
  │  └─────────────────────────────────────────────────────────────────────────────────┘   │
  │                                                                                        │
  │  Secrets (set in HF Space settings):                                                  │
  │  ├── GROQ_API_KEY                                                                     │
  │  ├── TAVILY_API_KEY                                                                   │
  │  ├── GITHUB_USERNAME                                                                  │
  │  └── GROQ_MODEL                                                                       │
  │                                                                                        │
  └────────────────────────────────────┬───────────────────────────────────────────────────┘
                                       │
                                       │ API Calls
                                       ▼
  ┌─── EXTERNAL SERVICES ──────────────────────────────────────────────────────────────────┐
  │                                                                                        │
  │  ┌───────────────────────┐  ┌──────────────────────┐  ┌─────────────────────────────┐ │
  │  │  Groq Cloud           │  │  Tavily API          │  │  GitHub REST API            │ │
  │  │                       │  │                      │  │                             │ │
  │  │  LLM: Llama 3.3 70B  │  │  Web search          │  │  Profile + repos            │ │
  │  │  Tool calling         │  │  (primary)           │  │  (public, no auth)          │ │
  │  │  Streaming            │  │                      │  │                             │ │
  │  │                       │  │  FREE: 1000/month    │  │  FREE: 60 req/hour          │ │
  │  │  FREE: 14,400 req/day │  │                      │  │  (no auth)                  │ │
  │  └───────────────────────┘  └──────────────────────┘  └─────────────────────────────┘ │
  │                                                                                        │
  │  ┌───────────────────────┐                                                            │
  │  │  DuckDuckGo           │                                                            │
  │  │  (fallback search)    │                                                            │
  │  │  FREE, no API key     │                                                            │
  │  └───────────────────────┘                                                            │
  │                                                                                        │
  └────────────────────────────────────────────────────────────────────────────────────────┘


  ┌─── GITHUB (Source Code) ───────────────────────────────────────────────────────────────┐
  │                                                                                        │
  │  Repo: github.com/iamabdullah1/personal-rag-llm-app                                  │
  │                                                                                        │
  │  Git Remotes:                                                                         │
  │  ├── origin       → GitHub (source code)                                              │
  │  └── huggingface  → HuggingFace Spaces (auto-deploys on push)                        │
  │                                                                                        │
  │  Push flow:                                                                           │
  │  git push origin main       → Updates GitHub                                          │
  │  git push huggingface main  → Triggers HF Space rebuild                               │
  │                                                                                        │
  └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. Error Handling & Recovery Matrix

### Every possible failure and how the system recovers

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   ERROR HANDLING & RECOVERY MATRIX                                        │
└──────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────┬──────────────────────────┬──────────────────────────────────┐
│ ERROR                      │ WHERE                    │ RECOVERY                          │
├────────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ Groq tool_use_failed       │ _call_groq()             │ Retry 3x → ToolCallError →       │
│                            │                          │ _fallback_answer() (no tools)    │
├────────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ Groq API timeout           │ _call_groq()             │ Retry 3x with backoff (1s, 2s)  │
│                            │                          │ → raise → SSE error event        │
├────────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ Groq rate limit (429)      │ _call_groq()             │ Retry with backoff →             │
│                            │                          │ error message to user            │
├────────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ ChromaDB search fails      │ search_personal_knowledge│ Return empty results,            │
│                            │                          │ LLM answers without personal ctx │
├────────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ Tavily search fails        │ search_web()             │ Fallback to DuckDuckGo           │
├────────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ DuckDuckGo also fails      │ search_web()             │ Return empty results,            │
│                            │                          │ LLM answers from training data   │
├────────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ GitHub API timeout         │ get_github_stats()       │ Return error message,            │
│                            │                          │ LLM says "couldn't fetch"        │
├────────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ Tool JSON parse error      │ _run_tool_loop()         │ arguments = {} (empty),          │
│                            │                          │ tool may still work              │
├────────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ SSE stream breaks          │ Frontend                 │ Finalization guard: if content    │
│                            │                          │ exists, show it anyway           │
├────────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ Backend hangs (no response)│ Frontend                 │ AbortController: 45s timeout     │
│                            │                          │ → "Request timed out"            │
├────────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ Rate limit exceeded        │ rate_limit_middleware     │ Return 429 JSON immediately      │
│                            │                          │ → Frontend shows error           │
├────────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ Invalid request body       │ Pydantic validation      │ Return 422 with details          │
├────────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ Any uncaught exception     │ SSE generator            │ Yield error event + done event   │
│                            │                          │ → Frontend always stops loading  │
└────────────────────────────┴──────────────────────────┴──────────────────────────────────┘


KEY PRINCIPLE: The user ALWAYS gets a response.

    Normal path:          Groq + tools → streaming answer ✅
    Tool calling fails:   Fallback mode → manual context + Groq (no tools) ✅
    API error:            Error message in chat bubble ✅
    Timeout:              "Request timed out" message ✅
    Stream breaks:        Finalization guard shows partial content ✅
```

---

## 14. Complete Example Walkthroughs

### Example A: Personal Question (Happy Path)

```
USER: "What are your main programming skills?"

  ┌─── FRONTEND ────────────────────────────────────────────────────────────────┐
  │  1. User clicks Send                                                        │
  │  2. POST /api/chat/stream { message: "What are your main...", session_id }  │
  │  3. Start 45s timeout                                                       │
  └─────────────────────────────────────────┬───────────────────────────────────┘
                                            ▼
  ┌─── BACKEND ─────────────────────────────────────────────────────────────────┐
  │  4. Middleware chain passes (CORS, rate limit, timing)                      │
  │  5. Cache check: 0.95 threshold → NO match (new question)                 │
  │  6. Get conversation history: [] (first message)                           │
  │  7. Build messages: [system_prompt, user_question]                         │
  │  8. Call Groq with 3 tools (non-streaming)                                 │
  └─────────────────────────────────────────┬───────────────────────────────────┘
                                            ▼
  ┌─── GROQ DECIDES ───────────────────────────────────────────────────────────┐
  │  9. LLM sees "your main programming skills" → personal question           │
  │  10. Calls: search_personal_knowledge("main programming skills")          │
  └─────────────────────────────────────────┬───────────────────────────────────┘
                                            ▼
  ┌─── TOOL EXECUTION ─────────────────────────────────────────────────────────┐
  │  11. Yield { tool_call: "search_personal_knowledge" }                      │
  │      → Frontend shows: 🔍 Searching knowledge base...                     │
  │  12. ChromaDB similarity search → 3 chunks from skills.txt                │
  │  13. Return JSON: { results: [...], count: 3 }                            │
  │  14. Append tool result to messages                                        │
  └─────────────────────────────────────────┬───────────────────────────────────┘
                                            ▼
  ┌─── ROUND 2 (GROQ) ────────────────────────────────────────────────────────┐
  │  15. Groq sees tool results → enough info → no more tools needed          │
  │  16. Break from tool loop → move to streaming phase                       │
  └─────────────────────────────────────────┬───────────────────────────────────┘
                                            ▼
  ┌─── STREAMING ──────────────────────────────────────────────────────────────┐
  │  17. Call Groq (streaming=True, no tools) with all messages               │
  │  18. Stream tokens:                                                        │
  │      → "I" → "specialize" → "in" → "several" → "programming" → ...      │
  │      → Frontend renders each token in real-time                            │
  │  19. Stream ends. full_answer = "I specialize in several..."              │
  └─────────────────────────────────────────┬───────────────────────────────────┘
                                            ▼
  ┌─── POST-PROCESSING ───────────────────────────────────────────────────────┐
  │  20. Store in conversation memory: [user_msg, assistant_msg]              │
  │  21. Cache Q&A pair: embedding + answer                                    │
  │  22. Yield { done: true, sources: [...], session_id: "..." }              │
  │      → Frontend: setLoading(false), clearTimeout                          │
  └─────────────────────────────────────────────────────────────────────────────┘

  TOTAL TIME: ~2-3 seconds
  TOKENS STREAMED: ~80-150
  TOOLS CALLED: 1 (search_personal_knowledge)
```

### Example B: General Knowledge (Web Search)

```
USER: "Explain how React hooks work"

  1.  Cache check → NO match
  2.  Groq decides: NOT about the person → search_web("React hooks how they work")
  3.  Frontend shows: 🌐 Searching the web...
  4.  Tavily returns 3 web results about React hooks
  5.  Groq sees results → generates answer with web context
  6.  Stream: "React hooks are functions that let you..."
  7.  Cache + store + done

  TOTAL TIME: ~3-4 seconds
  TOOLS CALLED: 1 (search_web)
```

### Example C: Cache Hit (Repeat Question)

```
USER: "What are your programming skills?"  (asked before as "main programming skills")

  1.  Cache check: similarity = 0.97 ≥ 0.95 → ✅ CACHE HIT
  2.  Stream cached answer word by word (20ms delay per word)
  3.  Store conversation, yield done

  TOTAL TIME: ~300ms ⚡ (vs 2-3s for full pipeline)
  TOOLS CALLED: 0
  GROQ API CALLS: 0
```

### Example D: Tool Calling Fails (Fallback)

```
USER: "What projects have you built?"

  1.  Cache check → NO match
  2.  Groq call with tools → "tool_use_failed" error
  3.  Retry #1 (wait 1s) → "tool_use_failed" again
  4.  Retry #2 (wait 2s) → "tool_use_failed" again
  5.  Raise ToolCallError
  6.  Frontend shows: 🔧 Processing...
  7.  FALLBACK MODE:
      a. Manually search ChromaDB → personal context
      b. Manually search Tavily → web context
      c. Build enriched prompt with all context
      d. Call Groq WITHOUT tools → generates answer
  8.  Stream answer word by word
  9.  Cache + store + done

  TOTAL TIME: ~6-8 seconds (retries + fallback)
  USER EXPERIENCE: Slightly slower, but still gets a great answer
```

### Example E: Multi-Tool Call

```
USER: "Tell me about your React projects and show me your GitHub"

  1.  Cache check → NO match
  2.  Groq decides: needs BOTH personal knowledge AND GitHub
  3.  Round 1:
      a. Call search_personal_knowledge("React projects")
         → Frontend: 🔍 Searching knowledge base...
      b. Call get_github_stats("iamabdullah1")
         → Frontend: 🐙 Checking GitHub...
      (Both tools execute)
  4.  Round 2: Groq sees both results → enough info → generate answer
  5.  Stream final answer combining personal + GitHub data

  TOTAL TIME: ~3-4 seconds
  TOOLS CALLED: 2 (parallel in same round)
```

---

## 📊 Performance Summary

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                         RESPONSE TIME BREAKDOWN (v2.0)                                    │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                           │
│   Cache Hit:                                                                             │
│   ├── Embedding Generation:     ~20ms                                                    │
│   ├── Cache Lookup:             ~5ms                                                     │
│   ├── Word-by-word streaming:   ~300ms (simulated)                                      │
│   └── TOTAL:                    ~350ms ⚡                                                │
│                                                                                           │
│   Single Tool Call (typical):                                                            │
│   ├── Cache Check:              ~25ms                                                    │
│   ├── Groq Round 1 (decide):    ~800ms                                                  │
│   ├── Tool Execution:           ~100ms (vector) / ~500ms (web) / ~300ms (GitHub)        │
│   ├── Groq Round 2 (stream):    ~1500ms (first token ~200ms, rest streamed)             │
│   ├── Post-processing:          ~20ms                                                    │
│   └── TOTAL:                    ~2-3 seconds                                             │
│                                                                                           │
│   Fallback Mode:                                                                         │
│   ├── Failed retries:           ~5000ms (3 attempts with backoff)                       │
│   ├── Manual tool execution:    ~600ms                                                   │
│   ├── Groq (no tools):          ~1500ms                                                  │
│   └── TOTAL:                    ~6-8 seconds                                             │
│                                                                                           │
│   Monthly Cost:                                                                          │
│   ├── Groq:      $0 (14,400 req/day free)                                               │
│   ├── Tavily:    $0 (1,000 searches/month free)                                         │
│   ├── GitHub:    $0 (public API)                                                         │
│   ├── Embeddings:$0 (local model)                                                        │
│   ├── HF Space:  $0 (free tier)                                                          │
│   ├── Vercel:    $0 (free tier)                                                          │
│   └── TOTAL:     $0.00 / month                                                           │
│                                                                                           │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

**Created for Abdullah Akram's Personal RAG Portfolio Application v2.0** 🚀

*Last Updated: February 26, 2026*
