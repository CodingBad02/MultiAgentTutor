# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
import uuid
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional, Dict, Any, List

# Import our multi-agent system
from .agents.tutor_agent import TutorAgent
from .agents.base_agent import TaskRequest

# Import utilities
from .utils.logger import setup_logger, get_logger
from .utils.session_manager import SessionManager

load_dotenv()

# Set up logging for the application
log_level = logging.INFO if os.getenv("ENVIRONMENT") != "production" else logging.WARNING
setup_logger(level=log_level)
logger = get_logger("main")

app = FastAPI(
    title="Multi-Agent AI Tutor", 
    description="AI Tutoring system with specialized agents for different subjects",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url=None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables")
    raise ValueError("GEMINI_API_KEY not found in environment variables.")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the multi-agent system and session manager
logger.info("Initializing Multi-Agent AI Tutor System")
tutor_agent = TutorAgent()
session_manager = SessionManager(max_history=5, expiry_seconds=3600)  # 1 hour session timeout
logger.info(f"System initialized with {len(tutor_agent.registry.agents)} specialist agents")

# API Models
class QueryRequest(BaseModel):
    query: str
    context: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    use_context_history: Optional[bool] = True

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    agent_used: str
    sources: list
    execution_time_ms: float
    session_id: str
    metadata: Dict[str, Any] = {}
    
class SessionInfo(BaseModel):
    session_id: str
    turn_count: int
    agents_used: List[str]
    duration_seconds: float

@app.get("/")
async def read_root():
    return {
        "message": "Multi-Agent AI Tutor is running!", 
        "version": "2.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "agents_loaded": len(tutor_agent.registry.agents)
    }

@app.post("/ask", response_model=QueryResponse)
async def ask_tutor(request: QueryRequest):
    """Process questions using the AI tutor system with tool capabilities and session history"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get conversation history if enabled
        context = request.context or ""
        if request.use_context_history:
            session_context = session_manager.get_context(session_id)
            if session_context:
                # Combine provided context with session history
                if context:
                    context = f"{context}\n\nConversation History:\n{session_context}"
                else:
                    context = f"Conversation History:\n{session_context}"
                logger.info(f"Using conversation history for session {session_id} ({len(session_context)} chars)")
        
        # Create and process task
        task = TaskRequest(
            query=request.query,
            context=context,
            user_id=request.user_id,
            session_id=session_id
        )
        response = tutor_agent.process_task(task)
        
        # Determine agent used
        agent_used = "AI Tutor Coordinator"
        if "delegated_to" in response.metadata:
            delegated_agent = tutor_agent.registry.get_agent(response.metadata["delegated_to"])
            if delegated_agent:
                agent_used = f"{delegated_agent.name}"
        
        # Add to session history
        session_manager.add_interaction(
            session_id=session_id,
            query=request.query,
            response=response.content,
            agent_used=agent_used
        )
        
        return QueryResponse(
            answer=response.content,
            confidence=response.confidence,
            agent_used=agent_used,
            sources=response.sources,
            execution_time_ms=response.execution_time_ms,
            session_id=session_id,
            metadata=response.metadata
        )
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/ask/{agent_type}", response_model=QueryResponse)
async def ask_specific_agent(agent_type: str, request: QueryRequest):
    """Directly ask a specific agent (math, physics) with session history"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get conversation history if enabled
        context = request.context or ""
        if request.use_context_history:
            session_context = session_manager.get_context(session_id)
            if session_context:
                # Combine provided context with session history
                if context:
                    context = f"{context}\n\nConversation History:\n{session_context}"
                else:
                    context = f"Conversation History:\n{session_context}"
                logger.info(f"Using conversation history for session {session_id} ({len(session_context)} chars)")
        
        # Create task with context
        task = TaskRequest(
            query=request.query,
            context=context,
            user_id=request.user_id,
            session_id=session_id
        )
        
        # Check if agent exists
        agent = tutor_agent.registry.get_agent(agent_type)
        if not agent:
            valid_agents = list(tutor_agent.registry.agents.keys())
            raise HTTPException(status_code=404, detail=f"Agent '{agent_type}' not found. Valid agents: {valid_agents}")
        
        # Process with specific agent
        response = agent.process_task(task)
        
        # Add to session history
        session_manager.add_interaction(
            session_id=session_id,
            query=request.query,
            response=response.content,
            agent_used=agent.name
        )
        
        return QueryResponse(
            answer=response.content,
            confidence=response.confidence,
            agent_used=agent.name,
            sources=response.sources,
            execution_time_ms=response.execution_time_ms,
            session_id=session_id,
            metadata=response.metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error with {agent_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error with {agent_type} agent: {str(e)}")

@app.get("/agents")
async def get_available_agents():
    """Get information about available specialist agents"""
    try:
        agents_info = {}
        for key, agent in tutor_agent.registry.agents.items():
            agents_info[key] = {
                "name": agent.name,
                "available_tools": agent.get_available_tools() if hasattr(agent, "get_available_tools") else []
            }
            
        return {
            "total_agents": len(agents_info),
            "agents": agents_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching agents: {str(e)}")

@app.get("/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get information about a specific session"""
    try:
        session_info = session_manager.get_session_info(session_id)
        if not session_info["exists"]:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found or expired")
            
        return SessionInfo(
            session_id=session_id,
            turn_count=session_info["turn_count"],
            agents_used=session_info["agents_used"],
            duration_seconds=session_info["duration_seconds"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching session: {str(e)}")

@app.post("/session/clear/{session_id}")
async def clear_session(session_id: str):
    """Clear session history for a specific session"""
    try:
        session_info = session_manager.get_session_info(session_id)
        if not session_info["exists"]:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found or expired")
            
        # Create empty session (effectively clearing history)
        session_manager.sessions[session_id] = {
            "history": [],
            "last_updated": time.time(),
            "agents_used": []
        }
            
        return {"status": "success", "message": f"Session '{session_id}' cleared successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)