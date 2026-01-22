from typing import Dict, List, Optional
import time
from collections import deque

class SessionManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.sessions: Dict[str, deque] = {}
            cls._instance.max_history = 10  # Keep last 10 turns
            cls._instance.session_expiry = 3600  # 1 hour expiry (not implemented yet, but good practice)
        return cls._instance
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        if session_id not in self.sessions:
            return []
        return list(self.sessions[session_id])
    
    def add_turn(self, session_id: str, user_query: str, ai_response: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = deque(maxlen=self.max_history)
        
        self.sessions[session_id].append({"role": "user", "content": user_query})
        self.sessions[session_id].append({"role": "assistant", "content": ai_response})
    
    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def format_history_for_llm(self, session_id: str) -> str:
        """Formats history as a string for LLM prompts"""
        history = self.get_history(session_id)
        if not history:
            return ""
            
        formatted = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)
