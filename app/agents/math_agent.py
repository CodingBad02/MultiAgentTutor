# app/agents/math_agent.py
import re
import time
from typing import List, Dict, Any
from .base_agent import BaseAgent, TaskRequest, AgentResponse
from ..utils.logger import AgentLogger
import google.generativeai as genai
import google.generativeai.types as gapic_types
from ..tools.equation_solver_tool import EquationSolverTool
from ..tools.formula_lookup_tool import FormulaLookupTool
from ..tools.base_tool import ToolResult


class MathAgent(BaseAgent):
    """
    Specialized agent for mathematics tutoring.
    Handles algebra, geometry, calculus, and arithmetic problems.
    """
    
    def __init__(self):
        super().__init__(
            name="Math Tutor",
            description="I am a specialized mathematics tutor with expertise in algebra, geometry, calculus, arithmetic, and mathematical problem-solving. I explain mathematical concepts step by step.",
            instruction="""You are a specialized Math Tutor agent. Your primary role is to help students understand and solve mathematical problems.
Explain concepts clearly and provide step-by-step solutions.
Focus on education and understanding.

You have access to tools that can help solve equations and look up formulas. Use these tools when appropriate to provide accurate answers."""
        )
        
        self.agent_logger = AgentLogger("Math Tutor")
        
        # Initialize tools
        self.equation_solver = EquationSolverTool()
        self.formula_lookup = FormulaLookupTool()
        
        # Register tools
        self.tools = [
            self.equation_solver,
            self.formula_lookup
        ]
        
        # For deployment compatibility, don't pre-configure tools
        # We'll initialize the model without tools and add them at runtime
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Store tool information for logging and runtime use
        self.function_declarations = []
        for tool in self.tools:
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
                self.function_declarations.append({
                    "name": tool.name,
                    "description": tool.description
                })
        
        self.math_keywords = [
            "math", "mathematics", "algebra", "geometry", "calculus", "arithmetic",
            "equation", "solve", "calculate", "compute", "formula", "derivative",
            "integral", "limit", "function", "graph", "polynomial", "quadratic",
            "linear", "exponential", "logarithm", "trigonometry", "sin", "cos", "tan",
            "triangle", "circle", "area", "perimeter", "volume", "angle", "degrees",
            "radians", "statistics", "probability", "matrix", "vector"
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
        """
        Get list of available tool names.
        """
        return [tool.name for tool in self.tools]
        
    def process_task(self, task: TaskRequest) -> AgentResponse:
        """
        Process a mathematics task using LLM with tool calling.
        """
        start_time = time.time()
        self.agent_logger.log_agent_start(task.query)
        flow_id = self.agent_logger.flow_id
        
        try:
            # Add tool information to the system prompt
            tools_info = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
            system_prompt = f"{self.get_system_prompt()}\n\nAvailable tools:\n{tools_info}"
            user_prompt = self._prepare_prompt_with_context(task)
            
            # Log available tools
            tool_names = [func_decl["name"] for func_decl in self.function_declarations]
            self.agent_logger.log_tool_schemas([{"name": name} for name in tool_names])
            self.agent_logger.log_gemini_request(user_prompt)
            
            # For deployment compatibility, handle tool calling manually
            # Let's first try to detect if this is a math problem that needs a tool
            needs_equation_solver = "solve" in task.query.lower() and any(x in task.query.lower() for x in ["equation", "="])
            needs_formula_lookup = "formula" in task.query.lower() or "what is the formula" in task.query.lower()
            
            # Call appropriate tool directly if needed
            tool_result = None
            tool_name = None
            tool_args = {}
            
            if needs_equation_solver:
                tool_name = "equation_solver"
                # Extract the equation from the query
                equation = task.query
                # Remove "solve" and "equation" words
                equation = equation.lower().replace("solve", "").replace("equation", "").strip()
                # Remove "what is x in" or similar phrases
                if "what is" in equation:
                    equation = equation.split("what is")[1].strip()
                if "x in" in equation:
                    equation = equation.split("x in")[1].strip()
                
                tool_args = {"equation": equation}
                tool_result = self._execute_tool(tool_name, tool_args)
                
            elif needs_formula_lookup:
                tool_name = "formula_lookup"
                # Extract the formula name from the query
                formula_query = task.query.lower()
                if "quadratic" in formula_query:
                    query = "quadratic_formula"
                elif "kinetic energy" in formula_query:
                    query = "kinetic_energy"
                elif "circle" in formula_query and "area" in formula_query:
                    query = "area_circle"
                elif "pythagorean" in formula_query:
                    query = "pythagorean_theorem"
                else:
                    # Just pass the whole query if we can't identify a specific formula
                    query = formula_query
                
                tool_args = {"query": query}
                tool_result = self._execute_tool(tool_name, tool_args)
            
            # If we used a tool, process the result
            if tool_result:
                final_response = self._process_tool_result_basic(task.query, tool_name, tool_args, tool_result)
            else:
                # Otherwise, use the model normally
                response = self.model.generate_content(user_prompt)
                final_response = response.text
            
            # Determine which tools were used for metadata
            used_tools = []
            if tool_name and tool_result and tool_result.success:
                used_tools.append(tool_name)
                self.agent_logger.log_tool_call(tool_name, tool_args, tool_result.result)
            
            self.agent_logger.log_gemini_response(final_response)
            
            execution_time = (time.time() - start_time) * 1000
            self.agent_logger.log_agent_complete(execution_time, 0.85)
            
            # Create metadata about tool usage
            metadata = {
                "agent": "Math Tutor",
                "flow_id": flow_id,
                "tools_available": self.get_available_tools(),
                "tools_used": used_tools,
                "tool_calls_count": len(used_tools)
            }
            
            return AgentResponse(
                content=final_response,
                confidence=0.85,
                sources=["Math Tutor", "Gemini 2.0 Flash"] + (used_tools if used_tools else []),
                execution_time_ms=execution_time,
                metadata=metadata
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
        """
        Execute a tool by name with the provided arguments.
        """
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.execute(**args)
        
        return ToolResult(
            success=False,
            result=None,
            error=f"Tool '{tool_name}' not found"
        )
    
    def _process_tool_result_basic(self, query: str, tool_name: str, tool_args: Dict[str, Any], tool_result: ToolResult) -> str:
        """
        Process the tool result with the model to generate a final response.
        Simplified version for better deployment compatibility.
        """
        # Create a regular model (without tools) to avoid issues
        processing_model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Format the result in a readable way
        result_str = str(tool_result.result)
        if isinstance(tool_result.result, dict):
            try:
                result_str = "\n".join([f"{k}: {v}" for k, v in tool_result.result.items()])
            except:
                pass
        
        # Prepare prompt for processing the tool result
        tool_output_prompt = f"""
You are a Math Tutor helping a student with the question: "{query}".

To solve this problem, you used the tool "{tool_name}" 
with arguments: {tool_args}

The tool returned this result: {result_str}

Based on this tool result, please provide a complete educational response that:
1. Explains what the tool did
2. Shows the step-by-step solution
3. Explains the mathematical concepts involved
4. Concludes with the final answer

Your goal is to help the student understand both the process and the answer.
"""
        
        # Process the tool result with a clean model
        try:
            result_response = processing_model.generate_content(tool_output_prompt)
            return result_response.text
        except Exception as e:
            # Fallback if there's an error
            return f"I found the answer to your question using my {tool_name}. The result is: {result_str}. Let me know if you need further explanation!"

# End of MathAgent