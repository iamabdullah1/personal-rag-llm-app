"""
Simplified RAG Service - Uses HuggingFace API (no local ML models)
Works with Python 3.14
"""
import requests
from app.services.vectorstore_simple import vectorstore_service
from app.services.conversation_store import conversation_store
from app.config import get_settings
from typing import Dict, Any, List
import uuid

settings = get_settings()


class RAGService:
    def __init__(self):
        # Using FREE HuggingFace Inference API
        self.api_url = "https://router.huggingface.co/v1/chat/completions"
        self.model = "Qwen/Qwen2.5-7B-Instruct"
        self.headers = {
            "Authorization": f"Bearer {settings.huggingface_api_key}",
            "Content-Type": "application/json"
        }
        
        # FIRST PERSON system prompt
        self.system_prompt = """You ARE the person whose portfolio this is. Always respond in FIRST PERSON.
Say "I have...", "My experience...", "I built..." - NOT "The developer has..." or "They have..."

You have personal context information about yourself including skills, projects, education, and hobbies.

RULES:
- For questions about YOU: Use the PERSONAL CONTEXT and speak as yourself
- Be friendly, confident, and authentic
- If personal info isn't available, say "I haven't shared that information yet" 
- Keep responses conversational and engaging

Example: "I've been programming for 5 years! My favorite language is Python."
"""
    
    def _call_huggingface(self, question: str, personal_context: str,
                          conversation_history: List[Dict[str, str]] = None) -> str:
        """Call HuggingFace Inference API"""
        
        # Build the combined context
        full_context = f"PERSONAL CONTEXT (about me):\n{personal_context}\n\n"
        
        # Build messages array
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history
        if conversation_history:
            recent_history = conversation_history[-6:]
            messages.extend(recent_history)
        
        # Add user question with context
        user_message = f"{full_context}Question: {question}"
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return f"I'm having trouble connecting right now. Please try again in a moment."
                
        except Exception as e:
            print(f"Error calling HuggingFace: {e}")
            return "I encountered an error. Please try again."
    
    async def get_answer(self, question: str, session_id: str = None,
                         conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Process a question and return answer with sources."""
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get personal context from documents
        relevant_docs = vectorstore_service.search(question, k=3)
        personal_context = "\n\n".join([doc["content"] for doc in relevant_docs])
        
        # If no relevant docs found, get all context
        if not personal_context:
            personal_context = vectorstore_service.get_all_context()[:2000]
        
        # Get stored conversation history if not provided
        if not conversation_history:
            conversation_history = conversation_store.get_history(session_id)
        
        # Generate answer
        answer = self._call_huggingface(
            question=question,
            personal_context=personal_context,
            conversation_history=conversation_history
        )
        
        # Store conversation
        conversation_store.add_message(session_id, "user", question)
        conversation_store.add_message(session_id, "assistant", answer)
        
        # Format sources
        sources = [
            {
                "content": doc["content"][:150] + "...",
                "source": doc["source"],
                "score": doc.get("score")
            }
            for doc in relevant_docs
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "session_id": session_id
        }


# Global instance
rag_service = RAGService()
