from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse, HealthResponse
from app.services.rag_service import rag_service
from datetime import datetime, timezone
import json
import asyncio

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc)
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
    Stream chat response for real-time typing effect.
    Uses Server-Sent Events (SSE) for streaming.
    """
    async def generate():
        try:
            # First, get context in parallel (fast operations)
            result = await rag_service.get_answer_streaming(
                question=request.message,
                session_id=request.session_id
            )
            
            # If cache hit, stream the cached answer
            if result.get("cache_hit"):
                answer = result["answer"]
                words = answer.split()
                for word in words:
                    yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                    await asyncio.sleep(0.02)  # Small delay for typing effect
                
                yield f"data: {json.dumps({'done': True, 'sources': result['sources'], 'session_id': result['session_id'], 'cache_hit': True})}\n\n"
                return
            
            # Stream from LLM
            async for chunk in rag_service.stream_llm_response(
                question=request.message,
                context=result.get("context", {}),
                session_id=result.get("session_id")
            ):
                if chunk.get("token"):
                    yield f"data: {json.dumps({'token': chunk['token']})}\n\n"
                elif chunk.get("done"):
                    yield f"data: {json.dumps({'done': True, 'sources': chunk.get('sources', []), 'session_id': chunk.get('session_id')})}\n\n"
                elif chunk.get("error"):
                    yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
