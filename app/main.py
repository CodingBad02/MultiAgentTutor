# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional, Dict, Any

# Import our multi-agent system
from .agents.tutor_agent import TutorAgent
from .agents.base_agent import TaskRequest

# Import logging
from .utils.logger import setup_logger, get_logger

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

# Initialize the multi-agent system
logger.info("Initializing Multi-Agent AI Tutor System")
tutor_agent = TutorAgent()
logger.info(f"System initialized with {len(tutor_agent.registry.agents)} specialist agents")

# API Models
class QueryRequest(BaseModel):
    query: str
    context: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    agent_used: str
    sources: list
    execution_time_ms: float
    metadata: Dict[str, Any] = {}

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
    """Process questions using the AI tutor system with tool capabilities"""
    try:
        # Create and process task
        task = TaskRequest(
            query=request.query,
            context=request.context,
            user_id=request.user_id,
            session_id=request.session_id
        )
        response = tutor_agent.process_task(task)
        
        # Determine agent used
        agent_used = "AI Tutor Coordinator"
        if "delegated_to" in response.metadata:
            delegated_agent = tutor_agent.registry.get_agent(response.metadata["delegated_to"])
            if delegated_agent:
                agent_used = f"{delegated_agent.name}"
        
        return QueryResponse(
            answer=response.content,
            confidence=response.confidence,
            agent_used=agent_used,
            sources=response.sources,
            execution_time_ms=response.execution_time_ms,
            metadata=response.metadata
        )
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/ask/{agent_type}", response_model=QueryResponse)
async def ask_specific_agent(agent_type: str, request: QueryRequest):
    """Directly ask a specific agent (math, physics)"""
    try:
        task = TaskRequest(
            query=request.query,
            context=request.context,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Check if agent exists
        agent = tutor_agent.registry.get_agent(agent_type)
        if not agent:
            valid_agents = list(tutor_agent.registry.agents.keys())
            raise HTTPException(status_code=404, detail=f"Agent '{agent_type}' not found. Valid agents: {valid_agents}")
        
        # Process with specific agent
        response = agent.process_task(task)
        
        return QueryResponse(
            answer=response.content,
            confidence=response.confidence,
            agent_used=agent.name,
            sources=response.sources,
            execution_time_ms=response.execution_time_ms,
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)