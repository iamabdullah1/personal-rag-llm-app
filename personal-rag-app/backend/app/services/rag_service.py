import httpx
import asyncio
from app.services.vectorstore import vectorstore_service
from app.services.conversation_store import conversation_store
from app.services.semantic_cache import semantic_cache
from app.config import get_settings
from typing import Dict, Any, List, AsyncGenerator
import uuid
from duckduckgo_search import DDGS
from concurrent.futures import ThreadPoolExecutor

settings = get_settings()

# Thread pool for CPU-bound operations
thread_pool = ThreadPoolExecutor(max_workers=4)


class RAGService:
    def __init__(self):
        # Using FREE HuggingFace Inference Providers API (OpenAI-compatible)
        self.api_url = "https://router.huggingface.co/v1/chat/completions"
        self.model = "Qwen/Qwen2.5-7B-Instruct"
        self.headers = {
            "Authorization": f"Bearer {settings.huggingface_api_key}",
            "Content-Type": "application/json"
        }
        
        # Connection pooling with httpx (async HTTP client)
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            headers=self.headers
        )
        
        # Initialize DuckDuckGo search (FREE, no API key needed)
        self.ddgs = DDGS()
        
        # FIRST PERSON system prompt with concise response guidelines
        self.system_prompt = """You ARE the person whose portfolio this is. Always respond in FIRST PERSON.
Say "I have...", "My experience...", "I built..." - NOT "The developer has..." or "They have..."

You have two sources of information:
1. PERSONAL CONTEXT: Information about yourself (skills, projects, hobbies, sports, life)
2. WEB SEARCH: General knowledge from the internet for technical/factual questions

## CRITICAL CONTENT RULES:
- **For introductions/about me:** Focus ONLY on professional info - education, skills, projects, work experience
- **NEVER mention sports, gym, fitness, hobbies, or co-curricular activities** unless the user EXPLICITLY asks about them
- Sports/hobbies are SEPARATE from professional identity - only share when directly asked
- Keep professional and personal life distinct

## RESPONSE LENGTH RULES:
- **Match your response length to the question complexity**
- Simple greeting/intro → 1-2 short sentences (20-40 words max)
- Specific question → Direct answer, 2-3 sentences (40-80 words)
- Detailed explanation request → Structured response with bullets (100-200 words)
- DO NOT over-explain or pad responses unnecessarily
- Get to the point quickly

## FORMATTING RULES:
- Use **bold** for emphasis on key points
- Use bullet points (- ) for lists
- Use numbered lists (1. 2. 3.) for steps or rankings
- Add blank lines between paragraphs for readability
- Keep paragraphs SHORT (2-3 sentences max)

## TONE:
- Be friendly, confident, and authentic
- Conversational but professional
- If personal info isn't available, say "I haven't shared that yet"

## EXAMPLES:

Q: "Hi" or "Hello" or "Tell me about yourself"
A: Hey! 👋 I'm Hamza, a Computer Science student at UMT specializing in **AI/ML and Data Science**. I build intelligent applications and love solving real-world problems with code.

Q: "What are your skills?"
A: I specialize in **Python**, **AI/ML**, **Data Science**, and **Web Development**. I work with frameworks like FastAPI, React, and tools like LangChain for building AI applications.

Q: "What sports do you play?" (ONLY answer about sports when directly asked like this)
A: I'm into **badminton** (played at National level!), **cricket**, and **snooker** at club level. Also hit the gym regularly - lost 30kg through consistent training! 💪
"""
    
    async def close(self):
        """Close HTTP client pool on shutdown."""
        await self.http_client.aclose()
    
    def _search_web_sync(self, query: str, max_results: int = 2) -> str:
        """Synchronous web search (runs in thread pool)."""
        try:
            results = self.ddgs.text(query, max_results=max_results)
            if results:
                web_context = "WEB SEARCH RESULTS:\n"
                for i, r in enumerate(results, 1):
                    body = r.get('body', '')[:150]
                    web_context += f"{i}. {r.get('title', '')}: {body}\n"
                return web_context
        except Exception as e:
            print(f"Web search error: {e}")
        return ""
    
    async def _search_web(self, query: str, max_results: int = 2) -> str:
        """Async web search using thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool, 
            self._search_web_sync, 
            query, 
            max_results
        )
    
    def _is_personal_question(self, question: str) -> bool:
        """Determine if the question is about the person or general knowledge."""
        personal_keywords = [
            "you", "your", "yourself", "portfolio", "project", "skill", "experience",
            "work", "job", "hobby", "sport", "education", "degree", "university",
            "built", "created", "developed", "favorite", "like", "love", "enjoy",
            "free time", "passion", "interest", "background", "about", "introduce",
            "who are", "tell me about", "what do you", "contact", "hire", "resume",
            "gym", "fitness", "cricket", "badminton", "snooker", "weight", "transformation"
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in personal_keywords)
    
    def _build_messages(self, question: str, personal_context: str, web_context: str,
                        conversation_history: List[Dict[str, str]] = None,
                        similar_cache: List[Dict] = None) -> List[Dict]:
        """Build messages array for LLM."""
        full_context = ""
        if personal_context:
            full_context += f"PERSONAL CONTEXT (about me):\n{personal_context}\n\n"
        
        if similar_cache:
            full_context += "SIMILAR PREVIOUS QUESTIONS & ANSWERS:\n"
            for i, cached in enumerate(similar_cache, 1):
                full_context += f"{i}. Q: {cached['question']}\nA: {cached['answer'][:200]}...\n\n"
        
        if web_context:
            full_context += f"{web_context}\n\n"
        
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if conversation_history:
            recent_history = conversation_history[-6:]
            messages.extend(recent_history)
        
        messages.append({
            "role": "user",
            "content": f"{full_context}Question: {question}"
        })
        
        return messages
    
    async def _call_huggingface_async(self, messages: List[Dict], stream: bool = False) -> str:
        """Async call to HuggingFace API with connection pooling."""
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.7,
            "stream": stream
        }
        
        response = await self.http_client.post(self.api_url, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"HuggingFace API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()
        
        return str(result)
    
    async def _get_context_parallel(self, question: str, session_id: str) -> Dict[str, Any]:
        """Get all context in parallel for faster response."""
        # Check cache first (fast)
        cached_answer = semantic_cache.get_exact_match(question)
        if cached_answer:
            return {
                "cache_hit": True,
                "answer": cached_answer,
                "session_id": session_id
            }
        
        # Run operations in parallel
        similar_cache_task = asyncio.get_event_loop().run_in_executor(
            thread_pool, semantic_cache.find_similar, question, 3
        )
        
        # Vector search (CPU-bound, use thread pool)
        def get_docs():
            retriever = vectorstore_service.get_retriever()
            return retriever.invoke(question)
        
        docs_task = asyncio.get_event_loop().run_in_executor(thread_pool, get_docs)
        
        # Wait for both
        similar_cache, docs = await asyncio.gather(similar_cache_task, docs_task)
        
        # Build personal context
        personal_context = "\n\n".join([doc.page_content for doc in docs])
        
        # Determine if we need web search
        is_personal = self._is_personal_question(question)
        web_context = ""
        
        if not is_personal or len(personal_context.strip()) < 50:
            web_context = await self._search_web(question)
        
        # Get conversation history (clean format for LLM)
        conversation_history = conversation_store.get_history_for_llm(session_id)
        
        return {
            "cache_hit": False,
            "similar_cache": similar_cache,
            "docs": docs,
            "personal_context": personal_context,
            "web_context": web_context,
            "conversation_history": conversation_history,
            "session_id": session_id
        }
    
    async def get_answer(self, question: str, session_id: str = None, 
                         conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Process a question and return answer with sources."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get context (parallel operations)
        context = await self._get_context_parallel(question, session_id)
        
        # Return cached answer if found
        if context.get("cache_hit"):
            # Store conversation even on cache hit to maintain history
            conversation_store.add_message(session_id, "user", question)
            conversation_store.add_message(session_id, "assistant", context["answer"])
            return {
                "answer": context["answer"],
                "sources": [{"content": "Retrieved from cache", "source": "Cache", "score": None}],
                "session_id": session_id,
                "cache_hit": True,
                "cache_type": "exact"
            }
        
        # Build messages and call LLM
        messages = self._build_messages(
            question,
            context["personal_context"],
            context["web_context"],
            conversation_history or context["conversation_history"],
            context["similar_cache"]
        )
        
        answer = await self._call_huggingface_async(messages)
        
        # Store conversation
        conversation_store.add_message(session_id, "user", question)
        conversation_store.add_message(session_id, "assistant", answer)
        
        # Cache the Q&A
        semantic_cache.add(question, answer)
        
        # Build sources
        sources = []
        for doc in context["docs"]:
            sources.append({
                "content": doc.page_content[:200] + "...",
                "source": doc.metadata.get("source", "Personal Profile"),
                "score": doc.metadata.get("score")
            })
        
        if context["similar_cache"]:
            sources.append({
                "content": f"Used {len(context['similar_cache'])} similar cached Q&As as context",
                "source": "Semantic Cache",
                "score": None
            })
        
        if context["web_context"]:
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
            "similar_cache_used": len(context["similar_cache"]) > 0
        }
    
    async def get_answer_streaming(self, question: str, session_id: str = None) -> Dict[str, Any]:
        """Get context for streaming response."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        context = await self._get_context_parallel(question, session_id)
        
        if context.get("cache_hit"):
            # Store conversation even on cache hit to maintain history
            conversation_store.add_message(session_id, "user", question)
            conversation_store.add_message(session_id, "assistant", context["answer"])
            return {
                "cache_hit": True,
                "answer": context["answer"],
                "sources": [{"content": "Retrieved from cache", "source": "Cache", "score": None}],
                "session_id": session_id
            }
        
        return {
            "cache_hit": False,
            "context": context,
            "session_id": session_id
        }
    
    async def stream_llm_response(self, question: str, context: Dict, 
                                   session_id: str) -> AsyncGenerator[Dict, None]:
        """Stream LLM response token by token."""
        try:
            messages = self._build_messages(
                question,
                context.get("personal_context", ""),
                context.get("web_context", ""),
                context.get("conversation_history"),
                context.get("similar_cache")
            )
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 300,
                "temperature": 0.7,
                "stream": True
            }
            
            full_answer = ""
            
            async with self.http_client.stream("POST", self.api_url, json=payload) as response:
                if response.status_code != 200:
                    yield {"error": f"API error: {response.status_code}"}
                    return
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_answer += content
                                    yield {"token": content}
                        except:
                            continue
            
            # Store conversation and cache
            conversation_store.add_message(session_id, "user", question)
            conversation_store.add_message(session_id, "assistant", full_answer)
            semantic_cache.add(question, full_answer)
            
            # Build sources
            sources = []
            for doc in context.get("docs", []):
                sources.append({
                    "content": doc.page_content[:200] + "...",
                    "source": doc.metadata.get("source", "Personal Profile"),
                    "score": None
                })
            
            yield {"done": True, "sources": sources, "session_id": session_id}
            
        except Exception as e:
            yield {"error": str(e)}


rag_service = RAGService()
