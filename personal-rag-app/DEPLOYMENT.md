# 🚀 Deployment Guide - Personal RAG Chatbot

## Architecture Overview

```
┌─────────────────┐         ┌─────────────────┐
│   FRONTEND      │         │    BACKEND      │
│   (Vercel)      │ ──API── │   (Railway)     │
│   React/Vite    │         │   FastAPI       │
└─────────────────┘         └─────────────────┘
                                    │
                            ┌───────┴───────┐
                            │   ChromaDB    │
                            │ (Vector Store)│
                            └───────────────┘
```

---

## Option 1: Railway + Vercel (Recommended) 🌟

### Step 1: Deploy Backend to Railway

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy Backend**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login
   railway login
   
   # Navigate to backend
   cd personal-rag-app/backend
   
   # Initialize and deploy
   railway init
   railway up
   ```

3. **Set Environment Variables** (Railway Dashboard → Variables)
   ```
   HUGGINGFACE_API_KEY=your_key_here
   ENVIRONMENT=production
   DEBUG=false
   ```

4. **Get Your Backend URL**
   - Railway will give you a URL like: `https://your-app.up.railway.app`

### Step 2: Deploy Frontend to Vercel

1. **Create Vercel Account**
   - Go to [vercel.com](https://vercel.com)
   - Sign up with GitHub

2. **Deploy Frontend**
   ```bash
   # Install Vercel CLI
   npm install -g vercel
   
   # Navigate to frontend
   cd personal-rag-app/frontend
   
   # Deploy
   vercel
   ```

3. **Set Environment Variable** (Vercel Dashboard → Settings → Environment Variables)
   ```
   VITE_API_URL=https://your-backend.up.railway.app
   ```

4. **Redeploy** to apply the env variable:
   ```bash
   vercel --prod
   ```

---

## Option 2: Single Deploy on Railway (Full Stack)

Deploy both frontend and backend as a single service:

### Step 1: Build Frontend into Backend

```bash
# Build frontend
cd frontend
npm run build

# Copy to backend static folder
mkdir -p ../backend/static
cp -r dist/* ../backend/static/
```

### Step 2: Update Backend to Serve Static Files

Add to `main.py`:
```python
from fastapi.staticfiles import StaticFiles

# Serve static files (frontend)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

### Step 3: Deploy to Railway

```bash
cd backend
railway up
```

---

## Option 3: Render (Free Alternative)

### Backend on Render

1. Go to [render.com](https://render.com)
2. New → Web Service → Connect GitHub repo
3. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables

### Frontend on Render (Static Site)

1. New → Static Site
2. **Build Command**: `npm run build`
3. **Publish Directory**: `dist`

---

## Environment Variables Reference

### Backend (.env)
| Variable | Required | Description |
|----------|----------|-------------|
| `HUGGINGFACE_API_KEY` | ✅ | Get from huggingface.co/settings/tokens |
| `ENVIRONMENT` | ❌ | `development` or `production` |
| `DEBUG` | ❌ | `true` or `false` |

### Frontend (Vercel/Render)
| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | ✅ | Your backend URL (e.g., `https://api.example.com`) |

---

## Post-Deployment Checklist

- [ ] Backend health check: `curl https://your-backend.up.railway.app/api/health`
- [ ] Frontend loads correctly
- [ ] Chat messages work
- [ ] Streaming responses work
- [ ] Conversation persistence works
- [ ] Rate limiting is active

---

## Troubleshooting

### CORS Errors
Add to backend `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### ChromaDB Persistence
On free tiers, the file system may reset. For production, consider:
- Railway Volumes (persistent storage)
- Pinecone (managed vector DB)
- Supabase pgvector

### Memory Issues
Free tiers have limited RAM. If the embeddings model fails:
- Use a smaller model
- Or use HuggingFace Inference API for embeddings too

---

## Cost Estimate

| Service | Free Tier | Paid |
|---------|-----------|------|
| Railway | 500 hrs/month | $5/month |
| Vercel | 100GB bandwidth | $20/month |
| Render | 750 hrs/month | $7/month |
| HuggingFace API | Free tier available | Pay per use |

**Total for portfolio project: $0/month** (within free tiers)

---

## Quick Deploy Commands

```bash
# Backend (Railway)
cd backend
railway login
railway init
railway up

# Frontend (Vercel)
cd frontend
vercel --prod
```

Your RAG chatbot will be live! 🎉
