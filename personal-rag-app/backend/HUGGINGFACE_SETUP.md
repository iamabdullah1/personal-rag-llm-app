# HuggingFace Setup Guide — v2.0

> **Note:** In v2.0, HuggingFace is used for TWO purposes:
> 1. **Embeddings** — all-MiniLM-L6-v2 model runs locally (via sentence-transformers)
> 2. **Deployment** — Backend hosted on HuggingFace Spaces (Docker)
>
> **The LLM has moved to Groq Cloud** (Llama 3.3 70B). HuggingFace is no longer used as the LLM provider.

---

## What Changed from v1.0?

| Aspect | v1.0 | v2.0 |
|--------|------|------|
| LLM Provider | HuggingFace Inference API (Qwen 2.5 7B) | Groq Cloud (Llama 3.3 70B) |
| Embeddings | HuggingFace all-MiniLM-L6-v2 (local) | Same (unchanged) |
| Deployment | Railway / Render | HuggingFace Spaces (Docker) |

## Embedding Model: all-MiniLM-L6-v2

This model runs **locally** — no API key needed, no cost, no latency.

| Feature | Details |
|---------|---------|
| Model | sentence-transformers/all-MiniLM-L6-v2 |
| Parameters | 22.7 million |
| Dimensions | 384 |
| Size | ~80 MB |
| Speed | ~14,000 sentences/sec |
| Runs On | CPU (locally) |
| Used For | ChromaDB vector search + Semantic cache |

### Installation

```bash
pip install sentence-transformers
```

The model is automatically downloaded on first use and cached locally.

## HuggingFace Spaces Deployment

The backend is deployed as a Docker container on HuggingFace Spaces.

### Setup

1. Create a Space at huggingface.co/spaces (SDK: Docker)
2. Set secrets (GROQ_API_KEY, TAVILY_API_KEY)
3. Push code via git

```bash
git remote add huggingface https://huggingface.co/spaces/YOUR_USERNAME/personal-rag-chatbot
git push huggingface main
```

### Important Notes

- HuggingFace Spaces uses port 7860 by default
- Free tier has cold starts (~30s after inactivity)
- Docker build includes the pre-ingested ChromaDB data
- Built frontend is served as static files from FastAPI

See [DEPLOYMENT.md](../DEPLOYMENT.md) for complete deployment instructions.

---

*Updated for v2.0 — HuggingFace now used for embeddings + deployment only*
