import requests
from app.services.vectorstore import vectorstore_service
from app.services.conversation_store import conversation_store
from app.services.semantic_cache import semantic_cache
from app.config import get_settings
from typing import Dict, Any, List
import uuid
from duckduckgo_search import DDGS

settings = get_settings()


class RAGService:
    def __init__(self):
        # Using FREE HuggingFace Inference Providers API (OpenAI-compatible)
        # Endpoint: https://router.huggingface.co/v1/chat/completions
        # Model: Qwen/Qwen2.5-7B-Instruct - FAST & FREE (switched from 72B for speed)
        self.api_url = "https://router.huggingface.co/v1/chat/completions"
        self.model = "Qwen/Qwen2.5-7B-Instruct"  # 7B = 10x faster than 72B
        self.headers = {
            "Authorization": f"Bearer {settings.huggingface_api_key}",
            "Content-Type": "application/json"
        }
        
        # Initialize DuckDuckGo search (FREE, no API key needed)
        self.ddgs = DDGS()
        
        # FIRST PERSON system prompt - respond AS the person
        self.system_prompt = """You ARE the person whose portfolio this is. Always respond in FIRST PERSON.
Say "I have...", "My experience...", "I built..." - NOT "The developer has..." or "They have..."

You have two sources of information:
1. PERSONAL CONTEXT: Information about yourself (skills, projects, hobbies, sports, life)
2. WEB SEARCH: General knowledge from the internet for technical/factual questions

RULES:
- For questions about YOU (skills, projects, hobbies, sports, life): Use PERSONAL CONTEXT and speak as yourself
- For general knowledge questions (what is X, how does Y work): Use WEB SEARCH results
- Be friendly, confident, and authentic
- If personal info isn't available, say "I haven't shared that information yet" 
- Keep responses conversational and engaging

Example personal response: "I've been playing cricket for 5 years! It's my favorite way to unwind after coding."
Example knowledge response: "Chemical engineering is a branch of engineering that combines chemistry, physics, and math to design processes for manufacturing chemicals, fuels, and other products."
"""
    
    def _search_web(self, query: str, max_results: int = 2) -> str:
        """Search the web using DuckDuckGo (FREE, no API key)."""
        try:
            results = self.ddgs.text(query, max_results=max_results)
            if results:
                web_context = "WEB SEARCH RESULTS:\n"
                for i, r in enumerate(results, 1):
                    # Truncate body to 150 chars for faster processing
                    body = r.get('body', '')[:150]
                    web_context += f"{i}. {r.get('title', '')}: {body}\n"
                return web_context
        except Exception as e:
            print(f"Web search error: {e}")
        return ""
    
    def _is_personal_question(self, question: str) -> bool:
        """Determine if the question is about the person or general knowledge."""
        personal_keywords = [
            "you", "your", "yourself", "portfolio", "project", "skill", "experience",
            "work", "job", "hobby", "sport", "education", "degree", "university",
            "built", "created", "developed", "favorite", "like", "love", "enjoy",
            "free time", "passion", "interest", "background", "about", "introduce",
            "who are", "tell me about", "what do you", "contact", "hire", "resume"
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in personal_keywords)
    
    def _call_huggingface(self, question: str, personal_context: str, web_context: str, 
                          conversation_history: List[Dict[str, str]] = None,
                          similar_cache: List[Dict] = None) -> str:
        """Call HuggingFace Inference Providers API (OpenAI-compatible format)."""
        
        # Build the combined context
        full_context = ""
        if personal_context:
            full_context += f"PERSONAL CONTEXT (about me):\n{personal_context}\n\n"
        
        # Add similar cached Q&As as context
        if similar_cache:
            full_context += "SIMILAR PREVIOUS QUESTIONS & ANSWERS:\n"
            for i, cached in enumerate(similar_cache, 1):
                full_context += f"{i}. Q: {cached['question']}\nA: {cached['answer'][:200]}...\n\n"
        
        if web_context:
            full_context += f"{web_context}\n\n"
        
        # Build messages array with conversation history
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history (last 6 messages for context)
        if conversation_history:
            # Only include last 6 messages to keep context manageable
            recent_history = conversation_history[-6:]
            messages.extend(recent_history)
        
        # Add current question with context
        messages.append({
            "role": "user",
            "content": f"{full_context}Question: {question}"
        })
        
        payload = {
            "model": self.model,
            "messages": messages,  # Use conversation history
            "max_tokens": 300,  # Reduced from 512 for faster responses
            "temperature": 0.7,
            "stream": False
        }
        
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"HuggingFace API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        # OpenAI-compatible response format
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()
        
        return str(result)
    
    async def get_answer(self, question: str, session_id: str = None, 
                         conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Process a question and return answer with sources."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # LEVEL 1: Check exact match cache (instant response)
        cached_answer = semantic_cache.get_exact_match(question)
        if cached_answer:
            return {
                "answer": cached_answer,
                "sources": [{"content": "Retrieved from cache", "source": "Cache", "score": None}],
                "session_id": session_id,
                "cache_hit": True,
                "cache_type": "exact"
            }
        
        # LEVEL 2: Find similar cached Q&As for context
        similar_cache = semantic_cache.find_similar(question, top_k=3)
        
        # Get conversation history from store
        if conversation_history is None:
            conversation_history = conversation_store.get_history(session_id)
        
        # Get relevant documents from personal context
        retriever = vectorstore_service.get_retriever()
        docs = retriever.invoke(question)
        
        # Build personal context from documents
        personal_context = "\n\n".join([doc.page_content for doc in docs])
        
        # Determine if we need web search
        web_context = ""
        is_personal = self._is_personal_question(question)
        
        # If not a personal question OR personal context seems insufficient, search web
        if not is_personal or len(personal_context.strip()) < 50:
            web_context = self._search_web(question)
        
        # Call HuggingFace API with ALL contexts: personal + web + similar cache + conversation
        answer = self._call_huggingface(question, personal_context, web_context, 
                                       conversation_history, similar_cache)
        
        # Store conversation in memory
        conversation_store.add_message(session_id, "user", question)
        conversation_store.add_message(session_id, "assistant", answer)
        
        # Save to semantic cache for future use
        semantic_cache.add(question, answer)
        
        # Extract sources
        sources = []
        for doc in docs:
            sources.append({
                "content": doc.page_content[:200] + "...",
                "source": doc.metadata.get("source", "Personal Profile"),
                "score": doc.metadata.get("score")
            })
        
        # Add cache source if similar Q&As were used
        if similar_cache:
            sources.append({
                "content": f"Used {len(similar_cache)} similar cached Q&As as context",
                "source": "Semantic Cache",
                "score": None
            })
        
        # Add web source if used
        if web_context:
            sources.append({
                "content": "Information from web search",
                "source": "DuckDuckGo Web Search",
                "score": None
            })
        
        return {
            "answer": answer,
            "sources": sources,
            "session_id": session_id,
            "cache_hit": False,
            "similar_cache_used": len(similar_cache) > 0
        }


rag_service = RAGService()
