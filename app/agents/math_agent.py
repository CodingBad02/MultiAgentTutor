# app/agents/math_agent.py
import time
from typing import List, Dict, Any
from .base_agent import BaseAgent, TaskRequest, AgentResponse
from ..utils.logger import AgentLogger
from ..tools.equation_solver_tool import EquationSolverTool
from ..tools.formula_lookup_tool import FormulaLookupTool
from ..tools.base_tool import ToolResult
import re


class MathAgent(BaseAgent):
    """
    Specialized agent for mathematics tutoring.
    Handles algebra, geometry, calculus, and arithmetic problems.
    """
    
    def __init__(self):
        super().__init__(
            name="Math Tutor",
            description="Math tutor with expertise in algebra, calculus, statistics, and geometry",
            instruction="""You are a Math Tutor agent. Help students understand mathematical concepts and solve problems.

STRICTLY Use available tools when appropriate:
- equation_solver: Solve algebraic equations
- formula_lookup: Find mathematical formulas

Provide clear explanations with step-by-step solutions."""
        )
        
        self.agent_logger = AgentLogger("Math Tutor")
        
        # Initialize tools
        self.equation_solver = EquationSolverTool()
        self.formula_lookup = FormulaLookupTool()
        self.tools = [self.equation_solver, self.formula_lookup]
        
        # Store tool schemas
        self.function_declarations = [{
            "name": tool.name,
            "description": tool.description
        } for tool in self.tools if hasattr(tool, 'name') and hasattr(tool, 'description')]
        
        # Keywords for confidence calculation
        self.math_keywords = [
            "math", "algebra", "calculus", "geometry", "statistics", "probability",
            "equation", "solve", "factor", "simplify", "compute", "calculate",
            "derivative", "integral", "function", "polynomial", "expression",
            "quadratic", "linear", "logarithm", "exponential", "trigonometry",
            "matrix", "vector", "variable", "coefficient", "inequality", 
            "sequence", "series", "sum", "arithmetic", "geometric",
            "mean", "median", "mode", "variance", "theorem", "proof",
            "fraction", "decimal", "percentage", "prime", "factor"
        ]
    
    def can_handle(self, query: str) -> float:
        """
        Determine if this agent can handle the math query.
        """
        query_lower = query.lower()
        keyword_score = sum(1 for keyword in self.math_keywords if keyword in query_lower)
        math_patterns = [
            r'\d+\s*[\+\-\*\/\^]\s*\d+',
            r'[xy]\s*[\+\-\*\/]\s*\d+',
            r'=',
            r'[xy]\^?\d*',
            r'sin|cos|tan|log|ln|sqrt',
            r'∫|∑|∆|π|θ|α|β|γ',
        ]
        pattern_score = sum(1 for pattern in math_patterns if re.search(pattern, query_lower))
        total_score = (keyword_score * 0.3) + (pattern_score * 0.7)
        max_possible_score = len(self.math_keywords) * 0.3 + len(math_patterns) * 0.7
        confidence = min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
        if any(word in query_lower for word in ["solve", "calculate", "compute", "equation", "formula"]):
            confidence = min(confidence + 0.3, 1.0)
        return confidence
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return [tool.name for tool in self.tools]
    
    def process_task(self, task: TaskRequest) -> AgentResponse:
        """Process a math task with tools for serverless compatibility"""
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
            
            # Detect if we need tools
            query_lower = task.query.lower()
            needs_equation_solver = any(x in query_lower for x in ["solve", "equation", "find x", "find the value"])
            needs_formula_lookup = any(x in query_lower for x in ["formula", "formula for"])
            
            # Call appropriate tool
            tool_result = None
            tool_name = None
            tool_args = {}
            used_tools = []
            
            if needs_equation_solver and self.equation_solver:
                tool_name = "equation_solver"
                tool_args = {"equation": task.query}
                tool_result = self._execute_tool(tool_name, tool_args)
            elif needs_formula_lookup and self.formula_lookup:
                tool_name = "formula_lookup"
                query = query_lower
                
                # Extract specific formula name if possible
                if "quadratic" in query:
                    formula = "quadratic_formula"
                elif "pythagorean" in query:
                    formula = "pythagorean_theorem"
                elif "area" in query and "circle" in query:
                    formula = "circle_area"
                elif "area" in query and "triangle" in query:
                    formula = "triangle_area"
                else:
                    formula = query
                
                tool_args = {"query": formula}
                tool_result = self._execute_tool(tool_name, tool_args)
            
            # Process result or use normal processing
            if tool_result and tool_result.success:
                final_response = self._process_tool_result(task.query, tool_name, tool_args, tool_result)
                used_tools = [tool_name]
                self.agent_logger.log_tool_call(tool_name, tool_args, tool_result.result)
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
                sources=["Math Tutor", "Gemini 2.0 Flash"] + used_tools,
                execution_time_ms=execution_time,
                metadata={
                    "agent": "Math Tutor",
                    "flow_id": flow_id,
                    "tools_used": used_tools,
                    "tool_calls_count": len(used_tools)
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.agent_logger.log_error(e, "processing math task")
            
            return AgentResponse(
                content=f"I encountered an error while trying to help with your math question: {str(e)}. Please try rephrasing.",
                confidence=0.1,
                execution_time_ms=execution_time,
                metadata={"error": str(e), "agent": "Math Tutor", "flow_id": flow_id}
            )

    # Removed _process_function_calls method
    # System prompt is now inherited from BaseAgent or can be overridden if needed
    # For now, relying on the simplified BaseAgent.get_system_prompt
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
You are a Math Tutor helping with: "{query}"

You used the tool "{tool_name}" and got this result: {result_str}

Provide an educational response that:
1. Explains the mathematical concepts involved
2. Shows how this applies to the question
3. Includes the answer in an easy to understand way
"""
        
        # Generate response
        try:
            result_response = self.model.generate_content(tool_output_prompt)
            return result_response.text
        except Exception as e:
            # Fallback
            return f"I found this solution for your math question: {result_str}. Let me know if you need further explanation!"

# End of MathAgent