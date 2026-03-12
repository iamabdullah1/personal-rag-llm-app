"""
Shared Tool Implementations for Agentic RAG Pipeline

These tools are used by:
1. FastAPI backend (via Groq tool calling) — async versions
2. MCP server (for Claude Desktop / Cursor) — exposed via MCP protocol

Tools:
- search_personal_knowledge: Search ChromaDB vector store
- search_web: Search via Tavily (fallback: DuckDuckGo)
- get_github_stats: Live GitHub profile + repos
"""

import json
import asyncio
import logging
import httpx
from typing import Dict, Any
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def search_personal_knowledge(query: str) -> Dict[str, Any]:
    """
    Search the personal knowledge base (ChromaDB) for information about
    skills, projects, education, work experience, hobbies, and personal background.
    
    Args:
        query: The search query to find relevant personal information
    
    Returns:
        Dict with results list and count
    """
    try:
        from app.services.vectorstore import vectorstore_service

        loop = asyncio.get_event_loop()
        retriever = vectorstore_service.get_retriever()
        docs = await loop.run_in_executor(None, retriever.invoke, query)

        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Personal Profile"),
                "category": doc.metadata.get("category", "general"),
                "topic": doc.metadata.get("topic", "unknown"),
                "document_title": doc.metadata.get("document_title", "Unknown"),
                "chunk_index": doc.metadata.get("chunk_index", -1),
            })

        if not results:
            return {"results": [], "message": "No relevant personal information found for this query."}

        return {"results": results, "count": len(results)}

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        return {"results": [], "error": f"Knowledge base search failed: {str(e)}"}


async def search_web(query: str) -> Dict[str, Any]:
    """
    Search the web for general knowledge, technical topics, current events,
    or any information not about the person's portfolio.
    
    Uses Tavily as primary search engine, DuckDuckGo as fallback.
    
    Args:
        query: The web search query
    
    Returns:
        Dict with results list and count
    """
    # Try Tavily first (reliable, designed for AI)
    if settings.tavily_api_key and settings.tavily_api_key != "your-tavily-api-key":
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=settings.tavily_api_key)
            response = client.search(query, max_results=3)
            results = []
            for r in response.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "content": r.get("content", "")[:400],
                    "url": r.get("url", "")
                })
            if results:
                logger.info(f"✅ Tavily search returned {len(results)} results")
                return {"results": results, "count": len(results), "source": "tavily"}
        except Exception as e:
            logger.warning(f"Tavily search error: {e}")

    # Fallback to DuckDuckGo
    try:
        from duckduckgo_search import DDGS
        ddgs = DDGS()
        loop = asyncio.get_event_loop()
        raw_results = await loop.run_in_executor(
            None, lambda: list(ddgs.text(query, max_results=3))
        )
        results = []
        for r in raw_results:
            results.append({
                "title": r.get("title", ""),
                "content": r.get("body", "")[:400],
                "url": r.get("href", "")
            })
        logger.info(f"✅ DuckDuckGo search returned {len(results)} results")
        return {"results": results, "count": len(results), "source": "duckduckgo"}
    except Exception as e:
        logger.warning(f"DuckDuckGo search also failed: {e}")
        return {"results": [], "error": f"Web search failed: {str(e)}"}


async def get_github_stats(username: str = "") -> Dict[str, Any]:
    """
    Get live GitHub profile and repository information.
    
    Args:
        username: GitHub username (defaults to configured username)
    
    Returns:
        Dict with profile info and recent repos
    """
    if not username:
        username = settings.github_username

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get user profile
            user_resp = await client.get(
                f"https://api.github.com/users/{username}",
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            if user_resp.status_code != 200:
                return {"error": f"GitHub user not found: {username} (status {user_resp.status_code})"}

            user = user_resp.json()

            # Get repos sorted by recently updated
            repos_resp = await client.get(
                f"https://api.github.com/users/{username}/repos",
                params={"sort": "updated", "per_page": 10, "direction": "desc"},
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            repos = repos_resp.json() if repos_resp.status_code == 200 else []

            return {
                "profile": {
                    "name": user.get("name"),
                    "bio": user.get("bio"),
                    "public_repos": user.get("public_repos"),
                    "followers": user.get("followers"),
                    "following": user.get("following"),
                    "url": user.get("html_url")
                },
                "recent_repos": [
                    {
                        "name": r.get("name"),
                        "description": r.get("description"),
                        "language": r.get("language"),
                        "stars": r.get("stargazers_count"),
                        "forks": r.get("forks_count"),
                        "url": r.get("html_url"),
                        "updated": r.get("updated_at")
                    }
                    for r in repos[:10]
                ]
            }

    except httpx.TimeoutException:
        return {"error": "GitHub API timed out. Please try again."}
    except Exception as e:
        logger.error(f"GitHub API failed: {e}")
        return {"error": f"GitHub API failed: {str(e)}"}
