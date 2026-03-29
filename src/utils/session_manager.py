from typing import Dict, List, Optional
import time
from collections import deque
import json
from pathlib import Path
from src.config import settings

class SessionManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.sessions: Dict[str, deque] = {}
            cls._instance.max_history = 10  # Keep last 10 turns
            cls._instance.session_expiry = 3600  # 1 hour expiry (not implemented yet, but good practice)
        return cls._instance

    def _get_session_file(self, session_id: str) -> Path:
        return settings.session_path / f"{session_id}.json"
        
    def _load_session(self, session_id: str) -> None:
        if session_id not in self.sessions:
            session_file = self._get_session_file(session_id)
            if session_file.exists():
                try:
                    with open(session_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.sessions[session_id] = deque(data, maxlen=self.max_history)
                except Exception:
                    self.sessions[session_id] = deque(maxlen=self.max_history)
            else:
                self.sessions[session_id] = deque(maxlen=self.max_history)

    def _save_session(self, session_id: str) -> None:
        if session_id in self.sessions:
            session_file = self._get_session_file(session_id)
            try:
                with open(session_file, "w", encoding="utf-8") as f:
                    json.dump(list(self.sessions[session_id]), f, indent=2)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to save session {session_id}: {e}")
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        self._load_session(session_id)
        if session_id not in self.sessions:
            return []
        return list(self.sessions[session_id])
    
    def add_turn(self, session_id: str, user_query: str, ai_response: str):
        self._load_session(session_id)
        
        self.sessions[session_id].append({"role": "user", "content": user_query})
        self.sessions[session_id].append({"role": "assistant", "content": ai_response})
        
        self._save_session(session_id)
    
    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        session_file = self._get_session_file(session_id)
        if session_file.exists():
            session_file.unlink()

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
