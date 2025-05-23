# app/agents/biology_agent.py
import time
from typing import List, Dict, Any
from .base_agent import BaseAgent, TaskRequest, AgentResponse
from ..utils.logger import AgentLogger

class BiologyAgent(BaseAgent):
    """Specialized agent for biology-related questions"""
    
    def __init__(self):
        super().__init__(
            name="Biology Tutor",
            description="Biology tutor with expertise in cellular biology, genetics, ecology, and human physiology",
            instruction="""You are a Biology Tutor agent. Help students understand biological concepts and processes.

Provide clear explanations with relevant examples and analogies.
Focus on accuracy and educational value in your responses."""
        )
        
        self.agent_logger = AgentLogger("Biology Tutor")
        
        # Keywords for confidence calculation
        self.biology_keywords = [
            "biology", "cell", "dna", "rna", "protein", "gene", "chromosome", "mitosis", "meiosis",
            "ecology", "ecosystem", "species", "evolution", "natural selection", "adaptation",
            "organism", "bacteria", "virus", "enzyme", "photosynthesis", "respiration",
            "anatomy", "physiology", "organ", "tissue", "blood", "heart", "brain", "nervous system",
            "digestion", "metabolism", "homeostasis", "hormone", "receptor", "immune",
            "plant", "animal", "fungi", "taxonomy", "biodiversity", "genetics"
        ]
    
    def can_handle(self, query: str) -> float:
        """Determine confidence level for handling a biology-related query (0.0-1.0)"""
        query_lower = query.lower()
        
        # Base confidence
        confidence = 0.2
        
        # Boost confidence based on keywords
        if any(keyword in query_lower for keyword in self.biology_keywords):
            confidence = min(confidence + 0.3, 0.8)
            
        # Further boost for specific biology topics
        if any(term in query_lower for term in ["cell", "dna", "gene", "protein", "enzyme"]):
            confidence = min(confidence + 0.2, 1.0)
            
        return confidence
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return []  # No specialized tools for this agent
    
    def process_task(self, task: TaskRequest) -> AgentResponse:
        """Process a biology-related task"""
        start_time = time.time()
        self.agent_logger.log_agent_start(task.query)
        flow_id = self.agent_logger.flow_id
        
        try:
            # Prepare prompts
            system_prompt = self.get_system_prompt()
            user_prompt = self._prepare_prompt_with_context(task)
            
            self.agent_logger.log_gemini_request(user_prompt)
            
            # Process with Gemini
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.model.generate_content(full_prompt)
            final_response = response.text
            
            self.agent_logger.log_gemini_response(final_response)
            execution_time = (time.time() - start_time) * 1000
            self.agent_logger.log_agent_complete(execution_time, 0.85)
            
            return AgentResponse(
                content=final_response,
                confidence=0.85,
                sources=["Biology Tutor", "Gemini 2.0 Flash"],
                execution_time_ms=execution_time,
                metadata={
                    "agent": "Biology Tutor",
                    "flow_id": flow_id,
                    "tools_used": [],
                    "tool_calls_count": 0
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.agent_logger.log_error(e, "processing biology task")
            
            return AgentResponse(
                content=f"I encountered an error while trying to help with your biology question: {str(e)}. Please try rephrasing.",
                confidence=0.1,
                execution_time_ms=execution_time,
                metadata={"error": str(e), "agent": "Biology Tutor", "flow_id": flow_id}
            )
    
    def get_system_prompt(self) -> str:
        """Get system prompt for Biology Tutor agent"""
        return f"""
{self.instruction}

As a Biology Tutor:
1. Provide clear explanations of biological processes
2. Use appropriate scientific terminology
3. Include relevant examples from nature
4. Make complex concepts accessible
"""
    
    def _prepare_prompt_with_context(self, task: TaskRequest) -> str:
        """Prepare user prompt with context if available"""
        if task.context:
            return f"Question: {task.query}\n\nContext: {task.context}"
        return f"Question: {task.query}"
