from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    result: Any
    error: str = ""
    metadata: Dict[str, Any] = {}


class BaseTool(ABC):
    """
    Base class for all tools that agents can use.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Return the tool's parameter schema for LLM function calling.
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema()
        }
    
    @abstractmethod
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        Return the JSON schema for this tool's parameters.
        """
        pass 