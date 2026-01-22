#!/usr/bin/env python3
"""
Test the full RAG pipeline for specific questions
"""
import asyncio
from app.services.rag_service import RAGService

async def test_rag_pipeline():
    rag_service = RAGService()

    try:
        # Test the problematic question
        print("=== Testing: 'about this project' ===")
        result = await rag_service.get_answer("about this project", "test_session")

        print(f"Answer: {result['answer'][:300]}...")
        print(f"Cache hit: {result.get('cache_hit', False)}")
        print(f"Sources: {len(result.get('sources', []))}")

        for i, source in enumerate(result.get('sources', []), 1):
            print(f"Source {i}: {source['source']} - {source['content'][:100]}...")

    finally:
        await rag_service.close()

if __name__ == "__main__":
    asyncio.run(test_rag_pipeline())