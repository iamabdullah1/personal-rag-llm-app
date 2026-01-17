from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.routers import chat
from app.config import get_settings
import logging
import time
from collections import defaultdict
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# ============================================
# RATE LIMITER (In-Memory for Development)
# ============================================
class RateLimiter:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, client_ip: str) -> bool:
        async with self.lock:
            now = time.time()
            minute_ago = now - 60
            
            # Clean old requests
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > minute_ago
            ]
            
            # Check limit
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                return False
            
            # Add current request
            self.requests[client_ip].append(now)
            return True

rate_limiter = RateLimiter(requests_per_minute=30)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered personal assistant API using RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================
# MIDDLEWARE
# ============================================

# GZip compression for responses > 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

# Configure CORS - Allow all origins for portfolio project
# For production with sensitive data, restrict to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for portfolio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for health checks
    if request.url.path == "/api/health":
        return await call_next(request)
    
    client_ip = request.client.host
    
    if not await rate_limiter.is_allowed(client_ip):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please wait a moment."}
        )
    
    response = await call_next(request)
    return response

# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.3f}s"
    return response

# Include routers
app.include_router(chat.router)


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Personal RAG API...")
    logger.info(f"📚 Debug mode: {settings.debug}")
    logger.info("⚡ Optimizations: GZip, Rate Limiting, Connection Pooling")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Shutting down Personal RAG API...")
    # Close HTTP client pool
    from app.services.rag_service import rag_service
    await rag_service.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
