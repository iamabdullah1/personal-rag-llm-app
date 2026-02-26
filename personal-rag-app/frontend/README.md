# Personal RAG Chatbot — Frontend

React-based chat interface with real-time SSE streaming, tool status indicators, and dark mode.

**Version:** 2.0.0

---

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| React 18 | UI framework |
| Vite | Build tool and dev server |
| Tailwind CSS | Styling |
| react-markdown | Markdown rendering in chat |
| remark-gfm | GitHub-flavored markdown |

## Features

- **SSE Streaming** — Real-time word-by-word response rendering
- **Tool Status Indicators** — Shows which tool the AI is using:
  - "Searching knowledge base..." (personal knowledge)
  - "Searching the web..." (web search)
  - "Fetching GitHub stats..." (GitHub API)
  - "Using tools..." (generic)
- **45-second Timeout** — AbortController prevents infinite loading
- **Dark/Light Mode** — Theme toggle with system preference detection
- **Session Management** — Persists session_id for conversation continuity
- **Mobile Responsive** — Works on all screen sizes
- **Markdown Support** — Renders formatted responses with code blocks
- **Error Handling** — Graceful error messages, never infinite loading

## Development

```bash
# Install dependencies
npm install

# Start dev server (proxies /api to localhost:8000)
npm run dev

# Build for production
npm run build
```

Dev server: http://localhost:5173

## API Integration

The frontend communicates with the backend via SSE streaming:

```
POST /api/chat/stream
Content-Type: application/json
Body: { "question": "...", "session_id": "..." }

SSE Response Events:
  data: {"tool_status": "Searching knowledge base..."}
  data: {"answer": "partial text"}
  data: {"done": true, "session_id": "abc123"}
```

## Proxy Configuration

- **Development**: Vite proxy in vite.config.js -> localhost:8000
- **Production**: Vercel rewrites in vercel.json -> HuggingFace Space

## Deployment

Deployed on **Vercel** with auto-deploy from GitHub.

See [DEPLOYMENT.md](../DEPLOYMENT.md) for details.
