#!/usr/bin/env python3
"""
Test script to check vector retrieval for specific questions
"""
from app.services.vectorstore import vectorstore_service

def test_retrieval(question):
    print(f"\n=== Testing retrieval for: '{question}' ===")

    retriever = vectorstore_service.get_retriever()
    docs = retriever.invoke(question)

    print(f"Retrieved {len(docs)} documents:")
    for i, doc in enumerate(docs, 1):
        print(f"\n{i}. Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"   Content preview: {doc.page_content[:200]}...")
        print(f"   Score: {doc.metadata.get('score', 'N/A')}")

if __name__ == "__main__":
    # Test the problematic question
    test_retrieval("about this project")

    # Test other questions for comparison
    test_retrieval("what are your skills")
    test_retrieval("tell me about yourself")