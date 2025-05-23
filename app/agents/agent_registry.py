# app/agents/agent_registry.py
from typing import Dict, List, Tuple, Optional
from .base_agent import BaseAgent
from .math_agent import MathAgent
from .physics_agent import PhysicsAgent
from .biology_agent import BiologyAgent


class AgentRegistry:
    """
    Registry for managing and discovering specialized agents.
    Follows Google ADK principles for agent orchestration.
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all available specialized agents."""
        # Create and register agents
        self.register_agent("math", MathAgent())
        self.register_agent("physics", PhysicsAgent())
        self.register_agent("biology", BiologyAgent())
        
        # Could add more agents here:
        # self.register_agent("chemistry", ChemistryAgent())
        # self.register_agent("history", HistoryAgent())
    
    def register_agent(self, key: str, agent: BaseAgent):
        """Register a new agent with the given key."""
        self.agents[key] = agent
    
    def get_agent(self, key: str) -> Optional[BaseAgent]:
        """Get a specific agent by key."""
        return self.agents.get(key)
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """Get all registered agents."""
        return self.agents.copy()
    
    def find_best_agent(self, query: str, threshold: float = 0.3) -> Tuple[Optional[BaseAgent], float]:
        """
        Find the best agent to handle the given query based on their can_handle method.
        This is a fallback or alternative routing mechanism.
        """
        best_agent = None
        best_confidence = 0.0
        
        for agent in self.agents.values():
            confidence = agent.can_handle(query)
            if confidence > best_confidence and confidence >= threshold:
                best_agent = agent
                best_confidence = confidence
        
        return best_agent, best_confidence
    
    def get_agent_capabilities(self) -> Dict[str, Dict[str, str]]:
        """
        Get a summary of all agent capabilities (name and description).
        """
        capabilities = {}
        for key, agent in self.agents.items():
            capabilities[key] = {
                "name": agent.name,
                "description": agent.description
            }
        return capabilities
    
    def route_query(self, query: str) -> Tuple[Optional[str], Optional[BaseAgent], float]:
        """
        Route a query to the most appropriate agent using the find_best_agent logic.
        Returns: Tuple of (agent_key, agent_instance, confidence_score)
        """
        best_agent, confidence = self.find_best_agent(query)
        
        if best_agent:
            for key, agent_instance in self.agents.items():
                if agent_instance is best_agent:
                    return key, best_agent, confidence
        
        return None, None, 0.0 