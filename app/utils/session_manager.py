# app/utils/session_manager.py
import time
import json
import os
from typing import Dict, List, Optional, Any
from ..utils.logger import get_logger

logger = get_logger("SessionManager")

# Flag to determine if we're running on Vercel
IS_VERCEL = os.environ.get('VERCEL', '0') == '1'

# Use Redis if available (for Vercel), otherwise use in-memory storage
try:
    import redis
    from urllib.parse import urlparse
    REDIS_URL = os.environ.get('REDIS_URL')
    redis_available = REDIS_URL is not None
    if redis_available:
        # Parse the Redis URL to extract components
        parsed_url = urlparse(REDIS_URL)
        redis_host = parsed_url.hostname
        redis_port = parsed_url.port or 6379
        redis_password = parsed_url.password
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True
        )
        # Test connection
        try:
            redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            redis_available = False
    else:
        redis_available = False
except ImportError:
    redis_available = False
    logger.info("Redis not available, using in-memory session storage")

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
        
        # Log storage method
        if redis_available:
            logger.info("Using Redis for persistent session storage")
        else:
            logger.info("Using in-memory session storage")
        
    def get_context(self, session_id: str) -> str:
        """Get formatted context history for a session"""
        if not session_id:
            return ""
        
        # Get session data from Redis or memory
        session_data = self._get_session(session_id)
        if not session_data:
            return ""
            
        # Check if session has expired
        if time.time() - session_data["last_updated"] > self.expiry_seconds:
            logger.info(f"Session {session_id} expired, clearing history")
            self._delete_session(session_id)
            return ""
            
        # Format conversation history
        history = session_data.get("history", [])
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
            
        # Get existing session or create new one
        session_data = self._get_session(session_id) or {
            "history": [],
            "last_updated": time.time(),
            "agents_used": []
        }
        
        # Add new interaction
        session_data["history"].append({
            "query": query,
            "response": response,
            "timestamp": time.time(),
            "agent_used": agent_used
        })
        
        # Track which agents have been used in this session
        if agent_used not in session_data["agents_used"]:
            session_data["agents_used"].append(agent_used)
            
        # Limit history length
        if len(session_data["history"]) > self.max_history:
            session_data["history"] = session_data["history"][-self.max_history:]
            
        # Update timestamp
        session_data["last_updated"] = time.time()
        
        # Save updated session
        self._save_session(session_id, session_data)
        
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get metadata about a session"""
        if not session_id:
            return {"exists": False}
            
        session_data = self._get_session(session_id)
        if not session_data:
            return {"exists": False}
        
        history = session_data.get("history", [])
        return {
            "exists": True,
            "turn_count": len(history),
            "agents_used": session_data.get("agents_used", []),
            "duration_seconds": time.time() - history[0]["timestamp"] if history else 0,
            "last_updated": session_data.get("last_updated", 0)
        }
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count of removed sessions"""
        # For Redis, we rely on key expiration
        if redis_available:
            return 0
            
        # For in-memory storage, we actively clean up
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
    
    # Helper methods for storage abstraction
    def _get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis or memory"""
        if redis_available:
            try:
                session_json = redis_client.get(f"session:{session_id}")
                if session_json:
                    return json.loads(session_json)
                return None
            except Exception as e:
                logger.error(f"Error retrieving session from Redis: {str(e)}")
                # Fall back to memory if Redis fails
                return self.sessions.get(session_id)
        else:
            return self.sessions.get(session_id)
    
    def _save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """Save session data to Redis or memory"""
        if redis_available:
            try:
                redis_client.set(
                    f"session:{session_id}", 
                    json.dumps(session_data),
                    ex=self.expiry_seconds  # Set expiration
                )
            except Exception as e:
                logger.error(f"Error saving session to Redis: {str(e)}")
                # Fall back to memory if Redis fails
                self.sessions[session_id] = session_data
        else:
            self.sessions[session_id] = session_data
    
    def _delete_session(self, session_id: str) -> None:
        """Delete session from Redis or memory"""
        if redis_available:
            try:
                redis_client.delete(f"session:{session_id}")
            except Exception as e:
                logger.error(f"Error deleting session from Redis: {str(e)}")
                # Fall back to memory if Redis fails
                if session_id in self.sessions:
                    del self.sessions[session_id]
        else:
            if session_id in self.sessions:
                del self.sessions[session_id]
