from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat
from app.config import get_settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered personal assistant API using RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "https://your-domain.vercel.app"  # Add your Vercel domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Personal RAG API...")
    logger.info(f"📚 Debug mode: {settings.debug}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Shutting down Personal RAG API...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
