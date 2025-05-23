# app/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import google.generativeai as genai
import time


class AgentResponse(BaseModel):
    content: str
    confidence: float
    sources: List[str] = []
    metadata: Dict[str, Any] = {}
    execution_time_ms: float = 0.0


class TaskRequest(BaseModel):
    query: str
    context: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class BaseAgent(ABC):
    """
    Base class for all agents in the multi-agent tutoring system.
    """
    
    def __init__(self, name: str, description: str, instruction: str, model_name: str = "gemini-2.0-flash"):
        self.name = name
        self.description = description
        self.instruction = instruction
        self.model = genai.GenerativeModel(model_name)
        
    @abstractmethod
    def can_handle(self, query: str) -> float:
        """
        Determine if this agent can handle the given query.
        Returns a confidence score between 0.0 and 1.0.
        """
        pass
    
    @abstractmethod
    def process_task(self, task: TaskRequest) -> AgentResponse:
        """
        Process the given task and return a response.
        """
        pass
    
    def get_system_prompt(self) -> str:
        """
        Generate the complete system prompt for this agent.
        """
        return f"""You are {self.name}.

{self.instruction}

{self.description}

Remember to:
- Provide clear, educational explanations
- Show your reasoning step by step
- Always aim to help the student understand concepts, not just provide answers
"""
    
    def _prepare_prompt_with_context(self, task: TaskRequest) -> str:
        """Prepare the user prompt with context."""
        context_section = ""
        if task.context:
            context_section = f"\n\nContext: {task.context}"
        
        return f"Student Question: {task.query}{context_section}" 