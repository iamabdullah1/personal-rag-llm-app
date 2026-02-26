# Conversation Memory System — v2.0

> **Status: Fully Implemented**

## Overview

The conversation memory system stores chat history per session, providing context to the LLM for follow-up questions.

## Architecture

```
User sends message with session_id
     |
     v
Conversation Store (in-memory dict)
     |
     +-- Retrieve last 6 messages for this session
     +-- Append to LLM messages: [system_prompt] + [history] + [question]
     |
     v
After response:
     +-- Store user message + AI response in session history
     +-- Trim to max 10 messages per session
     +-- Auto-cleanup sessions older than 24 hours
```

## Configuration

| Setting | Value | Location |
|---------|-------|----------|
| Max messages per session | 10 | config.py (max_conversations) |
| Messages sent to LLM | 6 (last 6) | rag_service.py |
| Session TTL | 24 hours (86400s) | config.py (conversation_ttl) |
| Storage | In-memory dict | conversation_store.py |
| Session ID | Auto-generated UUID if not provided | conversation_store.py |

## How It Works

1. **Client sends session_id** (or gets one auto-generated)
2. **Retrieve history**: Last 6 messages from the session
3. **Build LLM messages**: [system_prompt, ...history, user_question]
4. **After response**: Store both user message and AI response
5. **Trim**: Keep only last 10 messages per session
6. **Cleanup**: Remove sessions older than 24 hours

## Integration with Caching

The **semantic cache** (0.95 threshold) works alongside conversation memory:

- Cache is checked BEFORE building the message history
- If cache hits, the cached answer is streamed directly (no LLM call)
- Cached answers still get stored in conversation history
- This means cached answers maintain conversation context

### Cache Details

| Feature | Value |
|---------|-------|
| Threshold | 0.95 (cosine similarity) |
| Max entries | 1000 |
| TTL | 7 days |
| Eviction | LRU |
| Status | Fully implemented and working |

## Limitations

- **In-memory only**: Data lost on server restart
- **No persistence**: No database backing (by design, for simplicity)
- **Single instance**: No shared state between multiple server instances
- **No user auth**: Sessions are client-managed via session_id

## Future Improvements (Optional)

- Redis-backed storage for persistence
- User authentication for persistent history
- Conversation summarization for longer context windows
- Export/import conversation history

---

*Updated for v2.0 — Caching and memory are both fully implemented*
