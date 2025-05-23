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
    Follows Google ADK principles for agent design with function calling support.
    """
    
    def __init__(self, name: str, description: str, instruction: str, model_name: str = "gemini-2.0-flash"):
        self.name = name
        self.description = description
        self.instruction = instruction  # Core system instruction following ADK pattern
        self.model = genai.GenerativeModel(model_name)
        self.tools = []
        
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
    
    def add_tool(self, tool):
        """Add a tool to this agent's toolkit."""
        self.tools.append(tool)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get function declarations for all tools (for Gemini function calling)."""
        return [tool.get_schema() for tool in self.tools]
    
    def execute_tool(self, tool_name: str, **kwargs):
        """Execute a specific tool by name."""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.execute(**kwargs)
        raise ValueError(f"Tool '{tool_name}' not found")
    
    def get_system_prompt(self) -> str:
        """
        Generate the complete system prompt for this agent following ADK patterns.
        This is the core instruction that defines the agent's behavior.
        """
        tools_section = ""
        if self.tools:
            tool_descriptions = []
            for tool in self.tools:
                tool_descriptions.append(f"- {tool.name}: {tool.description}")
            tools_section = f"""

Available Tools:
{chr(10).join(tool_descriptions)}

When you need to use a tool, the system will handle the function calling automatically.
Explain what tool you're using and why before using it.
"""

        return f"""You are {self.name}.

{self.instruction}

{self.description}{tools_section}

Remember to:
- Provide clear, educational explanations
- Show your reasoning step by step
- Use tools when appropriate to provide accurate answers
- Always aim to help the student understand concepts, not just provide answers
"""
    
    def _prepare_prompt_with_context(self, task: TaskRequest) -> str:
        """Prepare the user prompt with context."""
        context_section = ""
        if task.context:
            context_section = f"\n\nContext: {task.context}"
        
        return f"Student Question: {task.query}{context_section}" 