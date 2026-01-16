from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse, HealthResponse
from app.services.rag_service import rag_service
from datetime import datetime
import json

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow()
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
            timestamp=datetime.utcnow()
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
    """
    async def generate():
        try:
            result = await rag_service.get_answer(
                question=request.message,
                session_id=request.session_id
            )
            
            # Stream the answer word by word
            words = result["answer"].split()
            for word in words:
                yield f"data: {json.dumps({'token': word + ' '})}\n\n"
            
            # Send final message with sources
            yield f"data: {json.dumps({'done': True, 'sources': result['sources']})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
