"""
In-memory conversation history storage
For production, use Redis or database
"""
from typing import Dict, List
from datetime import datetime, timedelta
import threading


class ConversationStore:
    """Store conversation history per session"""
    
    def __init__(self, max_history: int = 10, ttl_hours: int = 24):
        self.conversations: Dict[str, List[Dict]] = {}
        self.timestamps: Dict[str, datetime] = {}
        self.max_history = max_history  # Max messages to keep per session
        self.ttl_hours = ttl_hours  # Auto-delete old conversations
        self.lock = threading.Lock()
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to conversation history"""
        with self.lock:
            if session_id not in self.conversations:
                self.conversations[session_id] = []
            
            # Add new message
            self.conversations[session_id].append({
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Keep only last N messages
            if len(self.conversations[session_id]) > self.max_history:
                self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
            
            # Update timestamp
            self.timestamps[session_id] = datetime.utcnow()
            
            # Cleanup old sessions
            self._cleanup_old_sessions()
    
    def get_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        with self.lock:
            return self.conversations.get(session_id, [])
    
    def get_history_for_llm(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history formatted for LLM API (role + content only, no timestamp)"""
        with self.lock:
            history = self.conversations.get(session_id, [])
            return [{"role": m["role"], "content": m["content"]} for m in history]
    
    def clear_session(self, session_id: str):
        """Clear conversation history for a session"""
        with self.lock:
            if session_id in self.conversations:
                del self.conversations[session_id]
            if session_id in self.timestamps:
                del self.timestamps[session_id]
    
    def _cleanup_old_sessions(self):
        """Remove conversations older than TTL"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.ttl_hours)
        sessions_to_remove = [
            sid for sid, ts in self.timestamps.items()
            if ts < cutoff_time
        ]
        for sid in sessions_to_remove:
            self.conversations.pop(sid, None)
            self.timestamps.pop(sid, None)
    
    def get_stats(self) -> Dict:
        """Get statistics about stored conversations"""
        with self.lock:
            return {
                "active_sessions": len(self.conversations),
                "total_messages": sum(len(msgs) for msgs in self.conversations.values())
            }


# Global instance
conversation_store = ConversationStore(max_history=10, ttl_hours=24)
