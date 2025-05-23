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
        
        # Create combined tool schema for Google's function calling format
        self.tools_config = {
            "function_declarations": []
        }
        
        # Combine all tool schemas into a single config
        for tool in self.tools:
            tool_schema = tool.get_schema()
            if "function_declarations" in tool_schema and len(tool_schema["function_declarations"]) > 0:
                self.tools_config["function_declarations"].extend(tool_schema["function_declarations"])
        
        # Configure model with tool calling
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash',
            tools=[self.tools_config]
        )
        
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
            
            # Log available tools from function declarations
            tool_names = [func_decl["name"] for func_decl in self.tools_config["function_declarations"]]
            self.agent_logger.log_tool_schemas([{"name": name} for name in tool_names])
            self.agent_logger.log_gemini_request(user_prompt)
            
            # Generate content with tool calling enabled
            response = self.model.generate_content(
                user_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2
                )
            )
            
            # Check for function calls
            function_calls = []
            final_response = ""
            used_tools = []
            
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                # Extract function call details
                                function_call = part.function_call
                                function_calls.append(function_call)
                                tool_name = function_call.name
                                args = function_call.args
                                
                                # Log the function call
                                self.agent_logger.log_function_call_detected(tool_name, args)
                                
                                # Execute the tool
                                tool_result = self._execute_tool(tool_name, args)
                                used_tools.append(tool_name)
                                
                                # Log the tool result
                                self.agent_logger.log_tool_call(tool_name, args, tool_result.result)
                                
                                # Process the tool result with the model
                                final_response = self._process_tool_result(task.query, function_call, tool_result)
                            elif hasattr(part, 'text') and part.text:
                                # If there's regular text, use it
                                final_response = part.text
            else:
                # If no function calls detected, use the original response text
                final_response = response.text
            
            self.agent_logger.log_gemini_response(final_response)
            
            execution_time = (time.time() - start_time) * 1000
            self.agent_logger.log_agent_complete(execution_time, 0.85)
            
            # Create metadata about tool usage
            metadata = {
                "agent": "Math Tutor",
                "flow_id": flow_id,
                "tools_available": self.get_available_tools(),
                "tools_used": [fc.name for fc in function_calls] if function_calls else [],
                "tool_calls_count": len(function_calls)
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
    
    def _process_tool_result(self, query: str, function_call: Any, tool_result: ToolResult) -> str:
        """
        Process the tool result with the model to generate a final response.
        """
        # Create a regular model (without tools) to avoid infinite tool calls
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

To solve this problem, you used the tool "{function_call.name}" 
with arguments: {function_call.args}

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
            return f"I found the answer to your question using my equation solver. The result is: {result_str}. Let me know if you need further explanation!"

# End of MathAgent