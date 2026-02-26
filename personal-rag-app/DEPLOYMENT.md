# Deployment Guide — Personal RAG Chatbot v2.0

> **Backend on HuggingFace Spaces (Docker) + Frontend on Vercel**
> Total cost: $0/month

---

## Architecture

```
GitHub Repository (iamabdullah1/personal-rag-llm-app)
         |
         +----> HuggingFace Spaces (Backend - Docker)
         |        - FastAPI server
         |        - ChromaDB vector store
         |        - Groq LLM integration
         |        - URL: https://abdullah7570-personal-rag-chatbot.hf.space
         |
         +----> Vercel (Frontend - Static)
                  - React + Vite build
                  - Proxies /api/* to HuggingFace Space
                  - URL: https://personal-rag-chatbot.vercel.app
```

---

## 1. Backend Deployment (HuggingFace Spaces)

### Prerequisites
- HuggingFace account (free)
- Groq API key (free at console.groq.com)
- Tavily API key (free at tavily.com)

### Step 1: Create HuggingFace Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Settings:
   - **Name**: personal-rag-chatbot
   - **SDK**: Docker
   - **Visibility**: Public
   - **Hardware**: CPU Basic (free)

### Step 2: Set Environment Variables (Secrets)

In Space Settings > Repository secrets:

| Variable | Value | Required |
|----------|-------|----------|
| GROQ_API_KEY | gsk_... | Yes |
| TAVILY_API_KEY | tvly-dev-... | Yes |
| GROQ_MODEL | llama-3.3-70b-versatile | No (has default) |
| GITHUB_USERNAME | iamabdullah1 | No (has default) |

### Step 3: Connect Git Remote

```bash
# Add HuggingFace as a remote
git remote add huggingface https://huggingface.co/spaces/YOUR_USERNAME/personal-rag-chatbot

# Push to deploy
git push huggingface main
```

### Step 4: Verify Deployment

```bash
# Health check
curl https://YOUR_USERNAME-personal-rag-chatbot.hf.space/api/health

# Expected response:
# {"status":"healthy","version":"2.0.0"}
```

### Backend Dockerfile (backend/Dockerfile)

The backend Dockerfile:
- Uses Python 3.12
- Installs dependencies from requirements.txt
- Copies the app code, data, and pre-built frontend static files
- Exposes port 7860 (HuggingFace default)
- Runs with uvicorn

### Important Notes

- HuggingFace Spaces expects port 7860 by default
- The `start.sh` script handles the port configuration
- ChromaDB data is included in the Docker image (pre-ingested)
- The built frontend is served from `backend/static/`

---

## 2. Frontend Deployment (Vercel)

### Prerequisites
- Vercel account (free)
- GitHub repository connected

### Step 1: Import Project on Vercel

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Settings:
   - **Framework Preset**: Vite
   - **Root Directory**: frontend
   - **Build Command**: npm run build
   - **Output Directory**: dist

### Step 2: Configure Proxy (vercel.json)

The `frontend/vercel.json` file handles API proxying:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://abdullah7570-personal-rag-chatbot.hf.space/api/:path*"
    }
  ]
}
```

This ensures all `/api/*` requests from the frontend are forwarded to the HuggingFace Space backend.

### Step 3: Deploy

Vercel auto-deploys when you push to GitHub:

```bash
git push origin main
```

### Step 4: Verify

Visit your Vercel URL and test the chatbot.

---

## 3. Updating Both Platforms

### Deploy to Both at Once

```bash
# Commit changes
git add -A
git commit -m "Update: description of changes"

# Push to GitHub (triggers Vercel)
git push origin main

# Push to HuggingFace (triggers Space rebuild)
git push huggingface main
```

### Rebuild Frontend and Update Backend Static

When you change frontend code:

```bash
# Build frontend
cd frontend
npm run build

# Copy to backend static
rm -rf ../backend/static/*
cp -r dist/* ../backend/static/

# Commit and push both
cd ..
git add -A
git commit -m "Update frontend build"
git push origin main
git push huggingface main
```

---

## 4. Troubleshooting

### HuggingFace Space Not Starting

1. Check Space logs in the HuggingFace web UI
2. Verify all secrets are set correctly
3. Ensure Dockerfile exposes port 7860
4. Check that `start.sh` is executable

### Vercel API Calls Failing

1. Check vercel.json rewrites point to correct HF Space URL
2. Verify HF Space is running (check /api/health)
3. Check browser console for CORS errors
4. HF Space may need to wake up (free tier sleeps after inactivity)

### Common Issues

| Issue | Solution |
|-------|----------|
| HF Space sleeping | First request wakes it up (~30s cold start) |
| CORS errors | Backend allows all origins (*) |
| 504 Gateway Timeout | HF Space cold start, wait and retry |
| Rate limited | Groq: 14,400/day, Tavily: 1,000/month |
| Empty responses | Check GROQ_API_KEY is set in secrets |

---

## 5. Git Remotes Setup

```bash
# View current remotes
git remote -v

# Expected:
# origin    https://github.com/iamabdullah1/personal-rag-llm-app.git (push)
# huggingface https://huggingface.co/spaces/abdullah7570/personal-rag-chatbot (push)

# Add remotes if missing
git remote add origin https://github.com/iamabdullah1/personal-rag-llm-app.git
git remote add huggingface https://huggingface.co/spaces/abdullah7570/personal-rag-chatbot
```

---

## 6. Environment Variables Reference

### Backend (.env file for local development)

```env
GROQ_API_KEY=gsk_your_key_here
TAVILY_API_KEY=tvly-dev-your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GITHUB_USERNAME=iamabdullah1
```

### Production (HuggingFace Secrets)

Set these in Space Settings > Repository secrets. They are automatically available as environment variables in the Docker container.

---

*Deployment Guide v2.0 — Last Updated: June 2025*
