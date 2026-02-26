"""
Semantic Cache Service for RAG Application
- Level 1: Exact match cache (instant response)
- Level 2: Semantic similarity cache (similar Q&A as context)
"""

import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer


class SemanticCache:
    def __init__(
        self,
        similarity_threshold: float = 0.95,  # 95% similarity for exact match (prevents wrong cache hits)
        max_cache_size: int = 1000,
        ttl_hours: int = 168  # 7 days
    ):
        """
        Initialize semantic cache with exact match and similarity search
        
        Args:
            similarity_threshold: Minimum similarity (0-1) for exact match
            max_cache_size: Maximum number of cached Q&A pairs
            ttl_hours: Time to live for cache entries in hours
        """
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        self.ttl = timedelta(hours=ttl_hours)
        
        # Storage
        self.cache: Dict[str, Dict] = {}  # key -> {question, answer, embedding, timestamp, hit_count}
        self.lock = threading.Lock()
        
        # Load embedding model (same as vectorstore for consistency)
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        print(f"✅ Semantic Cache initialized (threshold={similarity_threshold}, max_size={max_cache_size})")
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        return self.embedder.encode(text, convert_to_numpy=True)
    
    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
    
    def _cleanup_old_entries(self):
        """Remove expired cache entries"""
        now = datetime.now()
        expired_keys = [
            key for key, data in self.cache.items()
            if now - data['timestamp'] > self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            print(f"🗑️  Cleaned up {len(expired_keys)} expired cache entries")
    
    def _cleanup_by_size(self):
        """Remove least used entries if cache is full"""
        if len(self.cache) >= self.max_cache_size:
            # Sort by hit_count (ascending) and remove bottom 10%
            sorted_items = sorted(
                self.cache.items(),
                key=lambda x: x[1]['hit_count']
            )
            remove_count = max(1, int(self.max_cache_size * 0.1))
            for key, _ in sorted_items[:remove_count]:
                del self.cache[key]
            print(f"🗑️  Removed {remove_count} least used cache entries")
    
    def get_exact_match(self, question: str) -> Optional[str]:
        """
        Check for exact match in cache (Level 1)
        
        Returns:
            Cached answer if similarity >= threshold, None otherwise
        """
        with self.lock:
            self._cleanup_old_entries()
            
            question_embedding = self._get_embedding(question.lower().strip())
            
            best_match = None
            best_similarity = 0.0
            
            for key, data in self.cache.items():
                similarity = self._cosine_similarity(question_embedding, data['embedding'])
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = data
            
            # Exact match if similarity >= threshold
            if best_match and best_similarity >= self.similarity_threshold:
                best_match['hit_count'] += 1
                print(f"⚡ EXACT CACHE HIT! Similarity: {best_similarity:.2%}")
                return best_match['answer']
            
            return None
    
    def find_similar(self, question: str, top_k: int = 3) -> List[Dict]:
        """
        Find similar cached Q&A pairs (Level 2)
        
        Args:
            question: User's question
            top_k: Number of similar Q&As to return
        
        Returns:
            List of similar Q&A dicts with similarity scores
        """
        with self.lock:
            if not self.cache:
                return []
            
            question_embedding = self._get_embedding(question.lower().strip())
            
            similarities = []
            for key, data in self.cache.items():
                similarity = self._cosine_similarity(question_embedding, data['embedding'])
                # Only include if above minimum threshold (but below exact match)
                if 0.60 <= similarity < self.similarity_threshold:
                    similarities.append({
                        'question': data['question'],
                        'answer': data['answer'],
                        'similarity': similarity
                    })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            results = similarities[:top_k]
            
            if results:
                sims = [f"{r['similarity']:.2%}" for r in results]
                print(f"🔍 Found {len(results)} similar cached Q&As (similarities: {sims})")
            
            return results
    
    def add(self, question: str, answer: str):
        """
        Add Q&A pair to cache
        
        Args:
            question: User's question
            answer: Generated answer
        """
        with self.lock:
            self._cleanup_by_size()
            
            question_clean = question.lower().strip()
            question_embedding = self._get_embedding(question_clean)
            
            # Use question hash as key
            key = str(hash(question_clean))
            
            self.cache[key] = {
                'question': question,
                'answer': answer,
                'embedding': question_embedding,
                'timestamp': datetime.now(),
                'hit_count': 0
            }
            
            print(f"💾 Cached Q&A pair (total: {len(self.cache)})")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self.lock:
            if not self.cache:
                return {
                    'total_entries': 0,
                    'total_hits': 0,
                    'avg_hits_per_entry': 0
                }
            
            total_hits = sum(data['hit_count'] for data in self.cache.values())
            return {
                'total_entries': len(self.cache),
                'total_hits': total_hits,
                'avg_hits_per_entry': total_hits / len(self.cache) if self.cache else 0,
                'most_hit_question': max(
                    self.cache.values(),
                    key=lambda x: x['hit_count']
                )['question'] if self.cache else None
            }
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()
            print("🗑️  Cache cleared")


# Global singleton instance
semantic_cache = SemanticCache(
    similarity_threshold=0.95,
    max_cache_size=1000,
    ttl_hours=168  # 7 days
)
