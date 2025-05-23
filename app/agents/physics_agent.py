# app/agents/physics_agent.py
import time
from typing import List, Dict, Any
from .base_agent import BaseAgent, TaskRequest, AgentResponse
from ..utils.logger import AgentLogger
from ..tools.formula_lookup_tool import FormulaLookupTool
from ..tools.base_tool import ToolResult


class PhysicsAgent(BaseAgent):
    """
    Specialized agent for physics tutoring.
    Handles mechanics, electricity, thermodynamics, and other physics concepts.
    """
    
    def __init__(self):
        super().__init__(
            name="Physics Tutor",
            description="Physics tutor with expertise in mechanics, electromagnetism, thermodynamics, and modern physics",
            instruction="""You are a Physics Tutor agent. Help students understand physics concepts and solve problems.

Use available tools when appropriate:
- formula_lookup: Find physics formulas and equations

Provide clear explanations with step-by-step solutions."""
        )
        
        self.agent_logger = AgentLogger("Physics Tutor")
        
        # Initialize tools
        self.formula_lookup = FormulaLookupTool()
        self.tools = [self.formula_lookup]
        
        # Store tool schemas
        self.function_declarations = [{
            "name": tool.name,
            "description": tool.description
        } for tool in self.tools if hasattr(tool, 'name') and hasattr(tool, 'description')]
        
        # Keywords for confidence calculation
        self.physics_keywords = [
            "physics", "force", "energy", "motion", "velocity", "acceleration", "momentum",
            "electric", "magnetic", "current", "voltage", "resistance", "circuit", 
            "thermodynamics", "temperature", "heat", "entropy", "pressure", "volume",
            "gravity", "mass", "weight", "friction", "kinetic", "potential", 
            "wave", "optics", "lens", "mirror", "refraction", "reflection", 
            "quantum", "atom", "relativity", "oscillation"
        ]
    
    def can_handle(self, query: str) -> float:
        """Determine confidence level for handling a physics-related query (0.0-1.0)"""
        query_lower = query.lower()
        
        # Base confidence
        confidence = 0.2
        
        # Boost confidence based on keywords
        if any(keyword in query_lower for keyword in self.physics_keywords):
            confidence = min(confidence + 0.3, 0.8)
            
        # Further boost for formula-related queries
        if any(term in query_lower for term in ["formula", "equation", "calculate"]):
            confidence = min(confidence + 0.2, 1.0)
            
        return confidence
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return [tool.name for tool in self.tools]
    
    def process_task(self, task: TaskRequest) -> AgentResponse:
        """Process a physics task with tools for serverless compatibility"""
        start_time = time.time()
        self.agent_logger.log_agent_start(task.query)
        flow_id = self.agent_logger.flow_id
        
        try:
            # Prepare prompts
            system_prompt = self.get_system_prompt()
            user_prompt = self._prepare_prompt_with_context(task)
            
            # Log tools
            if self.function_declarations:
                self.agent_logger.log_tool_schemas([{"name": tool.name} for tool in self.tools])
            self.agent_logger.log_gemini_request(user_prompt)
            
            # Detect if we need a formula lookup tool
            needs_formula = any(x in task.query.lower() for x in ["formula", "equation", "law of"])
            
            # Call formula lookup tool if needed
            tool_result = None
            tool_name = None
            tool_args = {}
            used_tools = []
            
            if needs_formula and self.formula_lookup:
                tool_name = "formula_lookup"
                query = task.query.lower()
                
                # Extract specific formula name if possible
                if "kinetic energy" in query:
                    formula = "kinetic_energy"
                elif "potential energy" in query:
                    formula = "potential_energy"
                elif "force" in query and ("newton" in query or "second law" in query):
                    formula = "force"
                elif "ohm" in query or "voltage" in query:
                    formula = "ohms_law"
                else:
                    formula = query
                
                tool_args = {"query": formula}
                tool_result = self._execute_tool(tool_name, tool_args)
                
                if tool_result and tool_result.success:
                    final_response = self._process_tool_result(task.query, tool_name, tool_args, tool_result)
                    used_tools = [tool_name]
                    self.agent_logger.log_tool_call(tool_name, tool_args, tool_result.result)
                else:
                    # Fallback to normal processing if tool failed
                    full_prompt = f"{system_prompt}\n\n{user_prompt}"
                    response = self.model.generate_content(full_prompt)
                    final_response = response.text
            else:
                # Normal processing without tools
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = self.model.generate_content(full_prompt)
                final_response = response.text
            
            self.agent_logger.log_gemini_response(final_response)
            execution_time = (time.time() - start_time) * 1000
            self.agent_logger.log_agent_complete(execution_time, 0.85)
            
            return AgentResponse(
                content=final_response,
                confidence=0.85, 
                sources=["Physics Tutor", "Gemini 2.0 Flash"] + used_tools,
                execution_time_ms=execution_time,
                metadata={
                    "agent": "Physics Tutor",
                    "flow_id": flow_id,
                    "tools_used": used_tools,
                    "tool_calls_count": len(used_tools)
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.agent_logger.log_error(e, "processing physics task")
            
            return AgentResponse(
                content=f"I encountered an error while trying to help with your physics question: {str(e)}. Please try rephrasing.",
                confidence=0.1,
                execution_time_ms=execution_time,
                metadata={"error": str(e), "agent": "Physics Tutor", "flow_id": flow_id}
            )

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name with provided arguments"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.execute(**args)
        
        return ToolResult(
            success=False,
            result=None,
            error=f"Tool '{tool_name}' not found"
        )
    
    def _process_tool_result(self, query: str, tool_name: str, tool_args: Dict[str, Any], tool_result: ToolResult) -> str:
        """Process the tool result with the model to generate a final response"""
        # Format result
        result_str = str(tool_result.result)
        if isinstance(tool_result.result, dict):
            try:
                result_str = "\n".join([f"{k}: {v}" for k, v in tool_result.result.items()])
            except:
                pass
        
        # Create prompt for processing result
        tool_output_prompt = f"""
You are a Physics Tutor helping with: "{query}"

You used the tool "{tool_name}" and got this result: {result_str}

Provide an educational response that:
1. Explains the physics concepts involved
2. Shows how this applies to the question
3. Includes the answer in an easy to understand way
"""
        
        # Generate response
        try:
            result_response = self.model.generate_content(tool_output_prompt)
            return result_response.text
        except Exception as e:
            # Fallback
            return f"I found this formula for your physics question: {result_str}. Let me know if you need further explanation!"
    
    def get_system_prompt(self) -> str:
        """
        Generate the complete system prompt for this agent following ADK patterns.
        This is the core instruction that defines the agent's behavior.
        """
        return f"""You are {self.name}.

{self.instruction}

{self.description}

Remember to:
- Use tools IMMEDIATELY when the query requires them (formulas → formula_lookup, calculations → calculator)
- Provide clear, educational explanations AFTER using tools
- Show your reasoning step by step with proper physics principles
- Always use correct units and verify physical reasonableness
- Always aim to help the student understand concepts, not just provide answers
""" 