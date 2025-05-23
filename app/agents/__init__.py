# app/agents/__init__.py
from .base_agent import BaseAgent, TaskRequest, AgentResponse
from .tutor_agent import TutorAgent
from .math_agent import MathAgent
from .physics_agent import PhysicsAgent
from .agent_registry import AgentRegistry
from .routing_functions import get_routing_function_declarations, get_routing_system_prompt

__all__ = [
    "BaseAgent", "TaskRequest", "AgentResponse",
    "TutorAgent", "MathAgent", "PhysicsAgent", "AgentRegistry",
    "get_routing_function_declarations", "get_routing_system_prompt"
] 