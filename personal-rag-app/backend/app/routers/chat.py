from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse, HealthResponse
from app.services.rag_service import rag_service
from app.services.conversation_store import conversation_store
from datetime import datetime, timezone
from typing import Optional
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """
    Fetch conversation history for a session.
    Used to restore chat on page reload.
    """
    try:
        history = conversation_store.get_history(session_id)
        return {
            "session_id": session_id,
            "messages": history,
            "message_count": len(history)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching conversation: {str(e)}"
        )


@router.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session."""
    try:
        conversation_store.clear_session(session_id)
        return {"status": "cleared", "session_id": session_id}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing conversation: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message and return AI response.
    
    - **message**: The user's question about the person
    - **session_id**: Optional session ID for conversation tracking
    - **conversation_history**: Optional conversation history for context
    """
    try:
        result = await rag_service.get_answer(
            question=request.message,
            session_id=request.session_id,
            conversation_history=request.conversation_history
        )
        
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            session_id=result["session_id"],
            timestamp=datetime.now(timezone.utc)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response using Server-Sent Events (SSE).
    Uses agentic tool calling: LLM decides which tools to use.
    """
    async def generate():
        try:
            async for event in rag_service.stream_answer(
                question=request.message,
                session_id=request.session_id,
                conversation_history=request.conversation_history
            ):
                yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield f"data: {json.dumps({'done': True, 'sources': [], 'session_id': request.session_id or ''})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Transfer-Encoding": "chunked"
        }
    )
