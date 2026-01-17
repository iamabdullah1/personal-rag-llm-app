"""
Simplified Vectorstore Service - No local ML models needed
Uses HuggingFace Inference API for embeddings
"""
import os
import json
from typing import List, Dict
from pathlib import Path

class SimpleVectorStore:
    """Simple file-based document store (no ML dependencies)"""
    
    def __init__(self, data_dir: str = "./data/personal"):
        self.data_dir = data_dir
        self.documents = []
        self._load_documents()
    
    def _load_documents(self):
        """Load text documents from data directory"""
        data_path = Path(self.data_dir)
        if not data_path.exists():
            print(f"⚠️ Data directory not found: {self.data_dir}")
            return
        
        for file_path in data_path.rglob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.documents.append({
                        "content": content,
                        "source": str(file_path.relative_to(data_path))
                    })
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        for file_path in data_path.rglob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.documents.append({
                        "content": content,
                        "source": str(file_path.relative_to(data_path))
                    })
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        print(f"✅ Loaded {len(self.documents)} documents")
    
    def search(self, query: str, k: int = 3) -> List[Dict]:
        """Simple keyword-based search (no ML needed)"""
        query_terms = query.lower().split()
        scored_docs = []
        
        for doc in self.documents:
            content_lower = doc["content"].lower()
            # Simple scoring: count matching terms
            score = sum(1 for term in query_terms if term in content_lower)
            if score > 0:
                scored_docs.append({
                    "content": doc["content"][:500],  # Truncate for context
                    "source": doc["source"],
                    "score": score
                })
        
        # Sort by score and return top k
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:k]
    
    def get_all_context(self) -> str:
        """Get all document content as context"""
        return "\n\n---\n\n".join([doc["content"] for doc in self.documents])


# Global instance
vectorstore_service = SimpleVectorStore()
