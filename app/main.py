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
from .agents.agent_registry import AgentRegistry
from .agents.base_agent import TaskRequest

# Import logging
from .utils.logger import setup_logger, get_logger

load_dotenv()

# Set up logging for the application
log_level = logging.INFO
if os.getenv("ENVIRONMENT") == "production":
    log_level = logging.WARNING
setup_logger(level=log_level)
logger = get_logger("main")

app = FastAPI(
    title="Multi-Agent AI Tutor", 
    description="AI Tutoring system with specialized agents for different subjects using Google ADK principles and Gemini 2.0 Flash",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# Add CORS middleware for web frontend support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
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

logger.info("🚀 Initializing Multi-Agent AI Tutor System")

# Initialize the multi-agent system
tutor_agent = TutorAgent()

logger.info(f"✅ System initialized with {len(tutor_agent.registry.agents)} specialist agents")

# Pydantic models for API
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

class RoutingInfoResponse(BaseModel):
    query: str
    routing_decision: Dict[str, Any]
    would_delegate: bool
    target_agent: Optional[str]
    reasoning: str

@app.get("/")
async def read_root():
    return {
        "message": "Multi-Agent AI Tutor is running!", 
        "version": "2.0.0",
        "features": [
            "Dynamic Gemini-based routing to specialist agents",
            "Function calling for routing decisions by TutorAgent",
            "Math and Physics specialist tutors",
            "General knowledge tutor capabilities",
            "Execution timing"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "agents_loaded": len(tutor_agent.registry.agents),
        "model": "gemini-2.0-flash",
        "routing_method": "gemini_function_calling"
    }

@app.post("/ask", response_model=QueryResponse)
async def ask_tutor(request: QueryRequest):
    """
    Main endpoint for asking questions to the AI tutor system.
    Uses Gemini's function calling for dynamic routing to specialists.
    """
    try:
        # Create task request
        task = TaskRequest(
            query=request.query,
            context=request.context,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Process through the tutor agent
        response = tutor_agent.process_task(task)
        
        # Determine which agent was actually used
        agent_used = "AI Tutor Coordinator"
        if "delegated_to" in response.metadata:
            delegated_agent = tutor_agent.registry.get_agent(response.metadata["delegated_to"])
            if delegated_agent:
                agent_used = f"{delegated_agent.name} (via Coordinator)"
        
        return QueryResponse(
            answer=response.content,
            confidence=response.confidence,
            agent_used=agent_used,
            sources=response.sources,
            execution_time_ms=response.execution_time_ms,
            metadata=response.metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/ask_direct/{agent_type}", response_model=QueryResponse)
async def ask_specific_agent(agent_type: str, request: QueryRequest):
    """
    Directly ask a specific agent type (math, physics, etc.)
    Bypasses the intelligent routing system.
    """
    try:
        agent = tutor_agent.registry.get_agent(agent_type.lower())
        if not agent:
            available_agents = list(tutor_agent.registry.agents.keys())
            raise HTTPException(
                status_code=404, 
                detail=f"Agent '{agent_type}' not found. Available agents: {available_agents}"
            )
        
        # Create task request
        task = TaskRequest(
            query=request.query,
            context=request.context,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Process directly with the specific agent
        response = agent.process_task(task)
        
        return QueryResponse(
            answer=response.content,
            confidence=response.confidence,
            agent_used=f"{agent.name} (Direct)",
            sources=response.sources,
            execution_time_ms=response.execution_time_ms,
            metadata=response.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/agents")
async def get_available_agents():
    """
    Get information about all available specialist agents.
    """
    try:
        capabilities = tutor_agent.get_available_specialists()
        return {
            "total_agents": len(capabilities),
            "routing_method": "gemini_function_calling",
            "agents": capabilities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving agents: {str(e)}")

@app.post("/routing_info", response_model=RoutingInfoResponse)
async def get_routing_info(request: QueryRequest):
    """
    Get information about how a query would be routed using Gemini's intelligence.
    Useful for debugging and understanding the dynamic routing system.
    """
    try:
        routing_info = tutor_agent.get_routing_info(request.query)
        
        if "error" in routing_info:
            raise HTTPException(status_code=500, detail=f"Routing analysis failed: {routing_info['error']}")
        
        return RoutingInfoResponse(
            query=routing_info["query"],
            routing_decision=routing_info["routing_decision"],
            would_delegate=routing_info["would_delegate"],
            target_agent=routing_info.get("target_agent"),
            reasoning=routing_info["reasoning"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting routing info: {str(e)}")

@app.post("/ask_gemini_direct", response_model=QueryResponse)
async def ask_gemini_direct(request: QueryRequest):
    """
    Legacy endpoint: Direct Gemini API call without agent system.
    Kept for comparison with the multi-agent approach.
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(request.query)
        return QueryResponse(
            answer=response.text,
            confidence=0.5,  # Default confidence for direct calls
            agent_used="Gemini Direct",
            sources=["Gemini 2.0 Flash"],
            execution_time_ms=0.0,  # Not measured for direct calls
            metadata={"mode": "direct_gemini", "bypass_agents": True}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with Gemini API: {str(e)}")

# Development/debugging endpoints
@app.get("/debug/agent_scores/{query}")
async def debug_agent_scores(query: str):
    """
    Debug endpoint to see how each agent scores a query (legacy confidence scoring).
    Note: Primary routing now uses Gemini's function calling, not confidence scores.
    """
    try:
        scores = {}
        for key, agent in tutor_agent.registry.agents.items():
            scores[key] = {
                "agent_name": agent.name,
                "legacy_confidence": agent.can_handle(query),  # Legacy scoring for comparison
                "tools": agent.get_available_tools()
            }
        
        # Also get the Gemini-based routing decision
        routing_info = tutor_agent.get_routing_info(query)
        
        return {
            "query": query,
            "note": "Primary routing uses Gemini function calling, not these legacy scores",
            "legacy_confidence_scores": scores,
            "gemini_routing_decision": routing_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in debug endpoint: {str(e)}")

@app.get("/system_prompts")
async def get_system_prompts():
    """
    Debug endpoint to view the system prompts used by each agent.
    """
    try:
        prompts = {}
        
        # Get the main coordinator prompt
        prompts["coordinator"] = {
            "name": tutor_agent.name,
            "instruction": tutor_agent.instruction,
            "description": tutor_agent.description
        }
        
        # Get specialist prompts
        for key, agent in tutor_agent.registry.agents.items():
            prompts[key] = {
                "name": agent.name,
                "instruction": agent.instruction,
                "description": agent.description,
                "full_system_prompt": agent.get_system_prompt()
            }
        
        return {
            "note": "These are the system prompts that guide each agent's behavior",
            "prompts": prompts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving system prompts: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)