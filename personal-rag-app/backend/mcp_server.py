"""
MCP Server — Personal RAG Knowledge Base

Exposes 3 tools via Model Context Protocol:
1. search_personal_knowledge — Search ChromaDB vector store
2. search_web — Search the internet (Tavily / DuckDuckGo)
3. get_github_stats — Live GitHub profile and repos

Usage:
  Local:         python mcp_server.py
  Claude Desktop: Add to claude_desktop_config.json (see below)

Claude Desktop Config (~/.claude/claude_desktop_config.json):
{
  "mcpServers": {
    "personal-rag": {
      "command": "python",
      "args": ["/path/to/backend/mcp_server.py"],
      "env": {
        "TAVILY_API_KEY": "your-key",
        "HUGGINGFACE_API_KEY": "your-key"
      }
    }
  }
}
"""

import sys
import os
import json
import asyncio

# Ensure the backend directory is in the Python path
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP

# Create MCP server
mcp = FastMCP(
    "personal-rag",
    description="Personal RAG knowledge base — search personal info, web, and GitHub"
)


@mcp.tool()
async def search_personal_knowledge(query: str) -> str:
    """
    Search Abdullah's personal knowledge base for information about his
    skills, projects, education, work experience, hobbies, sports, and background.
    
    Use this for any question about the person or their portfolio.
    
    Args:
        query: The search query to find relevant personal information
    """
    from app.services.tools import search_personal_knowledge as _search
    result = await _search(query)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def search_web(query: str) -> str:
    """
    Search the web for general knowledge, technical explanations, current events,
    or any factual information NOT about the person.
    
    Use for questions like 'What is React?', 'Latest AI news', 'How does FastAPI work?'
    
    Args:
        query: The web search query
    """
    from app.services.tools import search_web as _search
    result = await _search(query)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def get_github_stats(username: str = "iamabdullah1") -> str:
    """
    Get live GitHub profile and repository information for Abdullah.
    
    Use when asked about GitHub projects, repositories, contributions, or coding activity.
    
    Args:
        username: GitHub username (default: iamabdullah1)
    """
    from app.services.tools import get_github_stats as _get
    result = await _get(username)
    return json.dumps(result, indent=2, default=str)


if __name__ == "__main__":
    mcp.run()
