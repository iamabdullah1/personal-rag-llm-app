"""
Agentic RAG Service — Groq + Tool Calling

Flow:
1. User asks a question
2. Groq LLM receives the question + tool definitions
3. LLM decides: call tools or answer directly
4. If tools needed: execute tools → send results back → LLM generates final answer
5. Stream the answer to the frontend

Supports:
- Multi-round tool calling (up to 3 rounds)
- Retry logic with exponential backoff
- Semantic caching
- Conversation memory
- Streaming responses
"""

import json
import uuid
import asyncio
import logging
from groq import AsyncGroq
from app.services.tools import search_personal_knowledge, search_web, get_github_stats
from app.services.conversation_store import conversation_store
from app.services.semantic_cache import semantic_cache
from app.config import get_settings
from typing import Dict, Any, List, AsyncGenerator, Optional

logger = logging.getLogger(__name__)
settings = get_settings()


# ============================================
# TOOL DEFINITIONS (OpenAI-compatible format)
# ============================================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_personal_knowledge",
            "description": (
                "Search the personal knowledge base for information about Abdullah Akram — "
                "his skills, projects, education, work experience, hobbies, sports, contact info, "
                "and personal background. Use this for ANY question about the person or their portfolio."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant personal information"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search the web for general knowledge, technical explanations, current events, "
                "or any factual information NOT about the person. Use for questions like "
                "'What is React?', 'Latest AI news', 'How does FastAPI work?', etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The web search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_github_stats",
            "description": (
                "Get live GitHub profile and repository information for Abdullah. "
                "Use when asked about GitHub projects, repositories, contributions, or coding activity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "GitHub username (default: iamabdullah1)"
                    }
                },
                "required": []
            }
        }
    }
]

# Map tool names to async functions
TOOL_FUNCTIONS = {
    "search_personal_knowledge": search_personal_knowledge,
    "search_web": search_web,
    "get_github_stats": get_github_stats,
}


class ToolCallError(Exception):
    """Raised when Groq's tool calling fails due to model format issues."""
    pass


class RAGService:
    def __init__(self):
        self.settings = settings
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = settings.groq_model

        self.system_prompt = """You ARE the person whose portfolio this is. Always respond in FIRST PERSON.
Say "I have...", "My experience...", "I built..." — NOT "The developer has..." or "They have..."

You have access to tools:
1. **search_personal_knowledge** — searches your personal knowledge base (skills, projects, education, etc.)
2. **search_web** — searches the internet for general/technical questions
3. **get_github_stats** — gets your live GitHub profile and repos

## CRITICAL RULES:
- **ALWAYS use search_personal_knowledge** for questions about you, your skills, projects, education, work, hobbies
- **Use search_web** for general/technical questions not about you
- **Use get_github_stats** when asked about your GitHub, repos, or coding activity
- You can call MULTIPLE tools if a question needs both personal + web info
- **For introductions/about me:** Focus ONLY on professional info — education, skills, projects, work experience
- **NEVER mention sports, gym, fitness, hobbies** unless the user EXPLICITLY asks about them

## RESPONSE LENGTH RULES:
- Simple greeting/intro → 1-2 short sentences (20-40 words max)
- Specific question → Direct answer, 2-3 sentences (40-80 words)
- Detailed explanation → Structured response with bullets or numbered lists
- DO NOT over-explain or pad responses unnecessarily

## FORMATTING:
- Use **bold** for emphasis
- Use bullet points for lists
- Use numbered lists for steps
- Keep paragraphs SHORT (2-3 sentences max)

## TONE:
- Friendly, confident, authentic
- Conversational but professional
- If personal info isn't available, say "I haven't shared that yet"
"""

    async def _execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """Execute a tool and return JSON string result."""
        func = TOOL_FUNCTIONS.get(tool_name)
        if not func:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        try:
            result = await func(**arguments)
            return json.dumps(result, default=str)
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return json.dumps({"error": f"Tool execution failed: {str(e)}"})

    async def _call_groq(self, messages: List[Dict], tools: Optional[List] = None,
                         stream: bool = False, max_retries: int = 2):
        """Call Groq API with retry logic and exponential backoff."""
        for attempt in range(max_retries + 1):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.settings.max_tokens,
                    "temperature": 0.7,
                    "stream": stream,
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                return await self.client.chat.completions.create(**kwargs)

            except Exception as e:
                error_str = str(e)
                is_tool_error = "tool_use_failed" in error_str or "tool call validation" in error_str

                if is_tool_error:
                    logger.warning(f"Tool calling format error (attempt {attempt + 1}): {e}")
                    # On last attempt with tool error, raise ToolCallError so caller can fallback
                    if attempt == max_retries:
                        raise ToolCallError(str(e))
                else:
                    logger.warning(f"Groq API attempt {attempt + 1}/{max_retries + 1} failed: {e}")
                    if attempt == max_retries:
                        raise

                await asyncio.sleep(1.0 * (attempt + 1))  # 1s, 2s backoff

    def _build_messages(self, question: str,
                        conversation_history: Optional[List[Dict]] = None) -> List[Dict]:
        """Build message array for LLM with system prompt + history + question."""
        messages = [{"role": "system", "content": self.system_prompt}]

        if conversation_history:
            messages.extend(conversation_history[-6:])

        messages.append({"role": "user", "content": question})
        return messages

    async def _fallback_answer(self, question: str,
                               conversation_history: Optional[List[Dict]] = None) -> tuple:
        """
        Fallback when tool calling fails: manually gather context and call LLM directly.
        This ensures the user ALWAYS gets an answer even if Groq's tool calling is broken.
        """
        logger.info("⚠️ Using fallback mode (no tool calling)")
        sources = []

        # Manually gather context
        personal_context = ""
        web_context = ""

        try:
            personal_result = await search_personal_knowledge(question)
            if personal_result.get("results"):
                personal_context = "\n\n".join([r["content"] for r in personal_result["results"]])
                sources.append({"content": "Personal Knowledge Base", "source": "vector_db", "score": None})
        except Exception as e:
            logger.warning(f"Fallback: vector search failed: {e}")

        try:
            web_result = await search_web(question)
            if web_result.get("results"):
                web_context = "\n".join(
                    [f"- {r['title']}: {r['content']}" for r in web_result["results"]]
                )
                sources.append({"content": "Web Search", "source": "web_search", "score": None})
        except Exception as e:
            logger.warning(f"Fallback: web search failed: {e}")

        # Build context-enriched prompt
        context_parts = []
        if personal_context:
            context_parts.append(f"PERSONAL CONTEXT:\n{personal_context}")
        if web_context:
            context_parts.append(f"WEB SEARCH RESULTS:\n{web_context}")

        context_str = "\n\n".join(context_parts)
        enriched_question = f"{context_str}\n\nQuestion: {question}" if context_str else question

        # Build messages without tools
        messages = [{"role": "system", "content": self.system_prompt}]
        if conversation_history:
            messages.extend(conversation_history[-6:])
        messages.append({"role": "user", "content": enriched_question})

        # Call Groq WITHOUT tools
        response = await self._call_groq(messages, tools=None, stream=False)
        answer = response.choices[0].message.content or ""
        return answer, sources

    async def _run_tool_loop(self, messages: List[Dict]) -> tuple:
        """
        Run the agentic tool-calling loop:
        1. Send to LLM with tool definitions
        2. If LLM requests tools → execute them → send results back
        3. Repeat up to 3 rounds
        4. Return (final_answer, sources)
        """
        sources = []

        for round_num in range(3):
            response = await self._call_groq(messages, tools=TOOLS, stream=False)
            message = response.choices[0].message

            if not message.tool_calls:
                return message.content or "", sources

            # LLM wants to call tools — add the assistant message
            messages.append({
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            # Execute each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                logger.info(f"🔧 Tool call [{round_num + 1}]: {tool_name}({arguments})")
                result = await self._execute_tool(tool_name, arguments)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

                sources.append({
                    "content": f"Tool: {tool_name}",
                    "source": tool_name,
                    "score": None
                })

        # After max rounds, get final answer without tools
        response = await self._call_groq(messages, tools=None, stream=False)
        return response.choices[0].message.content or "", sources

    # ============================================
    # PUBLIC API: Non-Streaming
    # ============================================
    async def get_answer(self, question: str, session_id: str = None,
                         conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Process a question with agentic tool calling and return complete answer."""
        if not session_id:
            session_id = str(uuid.uuid4())

        # Check semantic cache first
        cached_answer = semantic_cache.get_exact_match(question)
        if cached_answer:
            conversation_store.add_message(session_id, "user", question)
            conversation_store.add_message(session_id, "assistant", cached_answer)
            return {
                "answer": cached_answer,
                "sources": [{"content": "Retrieved from cache", "source": "Semantic Cache", "score": None}],
                "session_id": session_id,
                "cache_hit": True
            }

        # Build messages with conversation history
        history = conversation_history or conversation_store.get_history_for_llm(session_id)
        messages = self._build_messages(question, history)

        try:
            try:
                answer, sources = await self._run_tool_loop(messages)
            except ToolCallError:
                logger.warning("Tool calling failed, using fallback mode")
                answer, sources = await self._fallback_answer(question, history)

            if not answer:
                answer = "I'm sorry, I couldn't generate a response. Please try again."

            # Store conversation (only once, here)
            conversation_store.add_message(session_id, "user", question)
            conversation_store.add_message(session_id, "assistant", answer)

            # Cache the Q&A
            semantic_cache.add(question, answer)

            return {
                "answer": answer,
                "sources": sources,
                "session_id": session_id,
                "cache_hit": False
            }

        except Exception as e:
            logger.error(f"RAG service error: {e}")
            raise

    # ============================================
    # PUBLIC API: Streaming
    # ============================================
    async def stream_answer(self, question: str, session_id: str = None,
                            conversation_history: List[Dict[str, str]] = None) -> AsyncGenerator[Dict, None]:
        """
        Stream an agentic answer:
        1. Check cache → stream cached answer word by word
        2. First Groq call (non-streaming) to handle tool decisions
        3. Execute tools if needed
        4. Final Groq call (streaming) for the answer with tool context
        5. Stream tokens to frontend via SSE
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        # Check semantic cache
        cached_answer = semantic_cache.get_exact_match(question)
        if cached_answer:
            conversation_store.add_message(session_id, "user", question)
            conversation_store.add_message(session_id, "assistant", cached_answer)
            words = cached_answer.split()
            for word in words:
                yield {"token": word + " "}
                await asyncio.sleep(0.02)
            yield {
                "done": True,
                "sources": [{"content": "Cached", "source": "Semantic Cache", "score": None}],
                "session_id": session_id
            }
            return

        # Build messages
        history = conversation_history or conversation_store.get_history_for_llm(session_id)
        messages = self._build_messages(question, history)
        sources = []

        try:
            tool_calling_failed = False

            try:
                # Phase 1: Tool-calling loop (non-streaming)
                for round_num in range(3):
                    response = await self._call_groq(messages, tools=TOOLS, stream=False)
                    message = response.choices[0].message

                    if not message.tool_calls:
                        if round_num == 0 and message.content:
                            # LLM answered directly (no tools) — stream word by word
                            answer = message.content
                            words = answer.split()
                            for word in words:
                                yield {"token": word + " "}
                                await asyncio.sleep(0.015)

                            conversation_store.add_message(session_id, "user", question)
                            conversation_store.add_message(session_id, "assistant", answer.strip())
                            semantic_cache.add(question, answer.strip())
                            yield {"done": True, "sources": sources, "session_id": session_id}
                            return
                        else:
                            # After tool calls, break to streaming phase
                            break

                    # LLM wants tools
                    messages.append({
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in message.tool_calls
                        ]
                    })

                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            arguments = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            arguments = {}

                        logger.info(f"🔧 Stream: {tool_name}({arguments})")
                        yield {"tool_call": tool_name}

                        result = await self._execute_tool(tool_name, arguments)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })
                        sources.append({
                            "content": f"Tool: {tool_name}",
                            "source": tool_name,
                            "score": None
                        })

            except ToolCallError:
                logger.warning("⚠️ Tool calling failed in stream, switching to fallback")
                tool_calling_failed = True

            if tool_calling_failed:
                # Fallback: gather context manually and stream
                yield {"tool_call": "fallback_search"}
                answer, sources = await self._fallback_answer(question, history)
                words = answer.split()
                for word in words:
                    yield {"token": word + " "}
                    await asyncio.sleep(0.015)

                conversation_store.add_message(session_id, "user", question)
                conversation_store.add_message(session_id, "assistant", answer.strip())
                semantic_cache.add(question, answer.strip())
                yield {"done": True, "sources": sources, "session_id": session_id}
                return

            # Phase 2: Stream the final answer (no tools)
            stream = await self._call_groq(messages, tools=None, stream=True)

            full_answer = ""
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_answer += content
                    yield {"token": content}

            if not full_answer:
                full_answer = "I'm sorry, I couldn't generate a response. Please try again."
                yield {"token": full_answer}

            # Store conversation and cache (only once)
            conversation_store.add_message(session_id, "user", question)
            conversation_store.add_message(session_id, "assistant", full_answer)
            semantic_cache.add(question, full_answer)

            yield {"done": True, "sources": sources, "session_id": session_id}

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {"error": f"Sorry, something went wrong: {str(e)}"}
            yield {"done": True, "sources": [], "session_id": session_id}


# Global singleton
rag_service = RAGService()
