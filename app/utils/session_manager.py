# app/utils/session_manager.py
import time
from typing import Dict, List, Optional, Any
from ..utils.logger import get_logger

logger = get_logger("SessionManager")

class SessionManager:
    """Manages conversation history for multi-turn interactions"""
    
    def __init__(self, max_history: int = 5, expiry_seconds: int = 3600):
        """
        Initialize the session manager
        
        Args:
            max_history: Maximum number of turns to keep in history
            expiry_seconds: How long sessions should live without activity
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_history = max_history
        self.expiry_seconds = expiry_seconds
        
    def get_context(self, session_id: str) -> str:
        """Get formatted context history for a session"""
        if not session_id or session_id not in self.sessions:
            return ""
            
        # Check if session has expired
        session = self.sessions[session_id]
        if time.time() - session["last_updated"] > self.expiry_seconds:
            logger.info(f"Session {session_id} expired, clearing history")
            del self.sessions[session_id]
            return ""
            
        # Format conversation history
        history = session["history"]
        if not history:
            return ""
            
        formatted_history = "\n".join([
            f"User: {turn['query']}\n"
            f"AI: {turn['response']}\n"
            for turn in history
        ])
        
        return formatted_history
        
    def add_interaction(self, session_id: str, query: str, response: str, agent_used: str) -> None:
        """Add a new interaction to the session history"""
        if not session_id:
            return
            
        # Create session if it doesn't exist
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],
                "last_updated": time.time(),
                "agents_used": []
            }
            
        session = self.sessions[session_id]
        
        # Add new interaction
        session["history"].append({
            "query": query,
            "response": response,
            "timestamp": time.time(),
            "agent_used": agent_used
        })
        
        # Track which agents have been used in this session
        if agent_used not in session["agents_used"]:
            session["agents_used"].append(agent_used)
            
        # Limit history length
        if len(session["history"]) > self.max_history:
            session["history"] = session["history"][-self.max_history:]
            
        # Update timestamp
        session["last_updated"] = time.time()
        
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get metadata about a session"""
        if not session_id or session_id not in self.sessions:
            return {"exists": False}
            
        session = self.sessions[session_id]
        return {
            "exists": True,
            "turn_count": len(session["history"]),
            "agents_used": session["agents_used"],
            "duration_seconds": time.time() - session["history"][0]["timestamp"] if session["history"] else 0,
            "last_updated": session["last_updated"]
        }
        
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count of removed sessions"""
        current_time = time.time()
        expired_ids = [
            sid for sid, session in self.sessions.items()
            if current_time - session["last_updated"] > self.expiry_seconds
        ]
        
        for sid in expired_ids:
            del self.sessions[sid]
            
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired sessions")
            
        return len(expired_ids)
