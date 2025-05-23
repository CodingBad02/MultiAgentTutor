# app/agents/math_agent.py
import re
import time
from typing import List
from .base_agent import BaseAgent, TaskRequest, AgentResponse
from ..tools.calculator_tool import CalculatorTool
from ..tools.equation_solver_tool import EquationSolverTool
from ..tools.formula_lookup_tool import FormulaLookupTool
from ..utils.logger import AgentLogger


class MathAgent(BaseAgent):
    """
    Specialized agent for mathematics tutoring following Google ADK patterns.
    Handles algebra, geometry, calculus, and arithmetic problems with tool integration.
    """
    
    def __init__(self):
        super().__init__(
            name="Math Tutor",
            description="I am a specialized mathematics tutor with expertise in algebra, geometry, calculus, arithmetic, and mathematical problem-solving. I can solve equations, perform calculations, look up formulas, and explain mathematical concepts step by step.",
            instruction="""You are a specialized Math Tutor agent. Your primary role is to help students understand and solve mathematical problems.


CRITICAL TOOL USAGE INSTRUCTIONS:
- For ANY equation with variables (like "solve 2x + 5 = 15" or "find x if x - 3 = 7"), you MUST use the "equation_solver" tool
- For numerical calculations and expressions, use the "calculator" tool
- For looking up mathematical formulas or constants, use the "formula_lookup" tool

TOOL USAGE PRIORITY:
1. If the problem contains an equation with variables (=, x, y), immediately use equation_solver
2. If it requires numerical computation, use calculator
3. If you need a formula or constant, use formula_lookup

When solving problems:
1. Identify what type of problem it is
2. IMMEDIATELY use the appropriate tool(s) - don't try to solve manually first
3. Explain the reasoning behind each step
4. Verify your answers when possible
5. Relate concepts to real-world applications when relevant

Always aim to educate, not just provide answers. Show your work and explain your reasoning, including why you chose specific tools."""
        )
        
        # Add math-specific tools
        self.add_tool(CalculatorTool())
        self.add_tool(EquationSolverTool()) 
        self.add_tool(FormulaLookupTool())
        
        # Set up logging
        self.agent_logger = AgentLogger("Math Tutor")
        
        # Keywords for basic confidence scoring (still useful as fallback)
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
        This is used as a fallback - primary routing is now done by Gemini.
        """
        query_lower = query.lower()
        
        # Check for math keywords
        keyword_score = sum(1 for keyword in self.math_keywords if keyword in query_lower)
        
        # Check for mathematical symbols and patterns
        math_patterns = [
            r'\d+\s*[\+\-\*\/\^]\s*\d+',  # Basic arithmetic
            r'[xy]\s*[\+\-\*\/]\s*\d+',   # Variables with numbers
            r'=',                         # Equations
            r'[xy]\^?\d*',               # Variables with exponents
            r'sin|cos|tan|log|ln|sqrt',  # Math functions
            r'∫|∑|∆|π|θ|α|β|γ',         # Math symbols
        ]
        
        pattern_score = sum(1 for pattern in math_patterns if re.search(pattern, query_lower))
        
        # Combine scores with higher weight on patterns
        total_score = (keyword_score * 0.3) + (pattern_score * 0.7)
        
        # Normalize to 0-1 range
        max_possible_score = len(self.math_keywords) * 0.3 + len(math_patterns) * 0.7
        confidence = min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
        
        # Boost confidence for clear math queries
        if any(word in query_lower for word in ["solve", "calculate", "compute", "equation", "formula"]):
            confidence = min(confidence + 0.3, 1.0)
        
        return confidence
    
    def process_task(self, task: TaskRequest) -> AgentResponse:
        """
        Process a mathematics task using Gemini with function calling for tools.
        """
        start_time = time.time()
        
        # Log agent start
        self.agent_logger.log_agent_start(task.query)
        
        try:
            # Get tool schemas for function calling
            tool_schemas = self.get_tool_schemas() if self.tools else []
            self.agent_logger.log_tool_schemas(tool_schemas)
            
            # Prepare the conversation
            system_prompt = self.get_system_prompt()
            user_prompt = self._prepare_prompt_with_context(task)
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            self.agent_logger.log_gemini_request(full_prompt)
            
            if tool_schemas:
                # Use function calling with tools
                self.agent_logger.logger.info("🔧 Using Gemini with function calling")
                
                try:
                    # Create tools configuration
                    tools_config = [{"function_declarations": tool_schemas}]
                    
                    # Make the API call with proper tools configuration
                    response = self.model.generate_content(
                        full_prompt,
                        tools=tools_config
                    )
                    
                    # Log the raw response structure
                    self.agent_logger.logger.info(f"📋 Response candidates: {len(response.candidates) if response.candidates else 0}")
                    if response.candidates and response.candidates[0].content.parts:
                        self.agent_logger.logger.info(f"📋 Response parts: {len(response.candidates[0].content.parts)}")
                    
                    # Process function calls if any
                    final_response = self._process_function_calls(response, task)
                    
                except Exception as tools_error:
                    self.agent_logger.log_error(tools_error, "using tools with Gemini")
                    # Fallback to no tools if there's an issue
                    self.agent_logger.logger.warning("🔄 Falling back to no-tools mode")
                    response = self.model.generate_content(full_prompt)
                    final_response = response.text
                    self.agent_logger.log_gemini_response(final_response)
                    
                    execution_time = (time.time() - start_time) * 1000
                    return AgentResponse(
                        content=final_response,
                        confidence=0.7,  # Lower confidence without tools
                        sources=["Math Agent", "Gemini 2.0 Flash"],
                        execution_time_ms=execution_time,
                        metadata={
                            "agent": "Math Agent",
                            "tools_available": self.get_available_tools(),
                            "tools_error": str(tools_error),
                            "fallback_mode": True
                        }
                    )
            else:
                # Fallback without tools
                self.agent_logger.logger.info("🔧 Using Gemini without tools (fallback)")
                response = self.model.generate_content(full_prompt)
                final_response = response.text
                self.agent_logger.log_gemini_response(final_response)
            
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log completion
            self.agent_logger.log_agent_complete(execution_time, 0.9)
            
            return AgentResponse(
                content=final_response,
                confidence=0.9,  # High confidence for math problems
                sources=["Math Agent", "Gemini 2.0 Flash"],
                execution_time_ms=execution_time,
                metadata={
                    "agent": "Math Agent",
                    "tools_available": self.get_available_tools(),
                    "system_prompt": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.agent_logger.log_error(e, "processing math task")
            
            return AgentResponse(
                content=f"I encountered an error while processing your math question: {str(e)}. Please try rephrasing your question.",
                confidence=0.1,
                execution_time_ms=execution_time,
                metadata={"error": str(e), "agent": "Math Agent"}
            )
    
    def _process_function_calls(self, response, task: TaskRequest) -> str:
        """
        Process any function calls made by Gemini and return the final response.
        """
        if not response.candidates or not response.candidates[0].content.parts:
            self.agent_logger.logger.warning("⚠️ No response parts found")
            return "I couldn't process your request properly. Please try again."
        
        response_parts = []
        function_calls_made = []
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                response_parts.append(part.text)
                self.agent_logger.logger.info(f"📝 Text part: {part.text[:100]}...")
            
            elif hasattr(part, 'function_call') and part.function_call:
                # Execute the function call
                func_call = part.function_call
                func_name = func_call.name
                func_args = dict(func_call.args)
                
                self.agent_logger.log_function_call_detected(func_name, func_args)
                
                try:
                    # Execute the tool
                    tool_result = self.execute_tool(func_name, **func_args)
                    
                    self.agent_logger.log_tool_call(func_name, func_args, tool_result.result if tool_result.success else tool_result.error)
                    
                    if tool_result.success:
                        response_parts.append(f"\n[Using {func_name}]: {tool_result.result}")
                        function_calls_made.append({
                            "tool": func_name,
                            "args": func_args,
                            "result": tool_result.result
                        })
                    else:
                        response_parts.append(f"\n[Tool Error]: {tool_result.error}")
                        
                except Exception as e:
                    self.agent_logger.log_error(e, f"executing tool {func_name}")
                    response_parts.append(f"\n[Tool Execution Error]: {str(e)}")
        
        # Log if no function calls were made but tools were available
        if not function_calls_made and self.tools:
            self.agent_logger.logger.warning("⚠️ No function calls made despite tools being available")
            
            # Check if this is an equation that should use the equation solver
            if "=" in task.query and any(var in task.query.lower() for var in ["x", "y", "solve"]):
                self.agent_logger.logger.info("🔍 Detected equation - manually calling equation solver")
                try:
                    # Extract the equation
                    equation_match = re.search(r'[^=]+=\s*[^=]+', task.query)
                    if equation_match:
                        equation = equation_match.group().strip()
                        tool_result = self.execute_tool("equation_solver", equation=equation)
                        if tool_result.success:
                            response_parts.append(f"\n[Manual equation solving]: {equation} → x = {tool_result.result}")
                            function_calls_made.append({
                                "tool": "equation_solver",
                                "args": {"equation": equation},
                                "result": tool_result.result
                            })
                except Exception as e:
                    self.agent_logger.log_error(e, "manual equation solving")
        
        # Combine all parts and send back through Gemini for final formatting
        raw_response = "\n".join(response_parts)
        self.agent_logger.logger.info(f"🔄 Function calls made: {len(function_calls_made)}")
        
        # Send the response back through Gemini for better formatting and explanation
        formatting_prompt = f"""Please format and explain this mathematical solution clearly for a student:

Original Question: {task.query}

Solution Process: {raw_response}

Tool Results Used: {function_calls_made}

Please provide a clear, step-by-step explanation that helps the student understand both the process and the final answer. Make sure to explain what tools were used and why."""

        try:
            self.agent_logger.log_gemini_request(formatting_prompt)
            formatted_response = self.model.generate_content(formatting_prompt)
            final_content = formatted_response.text
            self.agent_logger.log_gemini_response(final_content)
            return final_content
        except Exception as e:
            self.agent_logger.log_error(e, "formatting response")
            # Fallback to raw response if formatting fails
            return raw_response 

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

CRITICAL: You MUST use these tools when appropriate:
- For ANY equation with variables (like "solve 2x + 5 = 15"), immediately call equation_solver
- For numerical calculations (like "calculate 2.5 * 8 + sqrt(16)"), immediately call calculator  
- For formula requests (like "what is the quadratic formula"), immediately call formula_lookup

Do NOT solve equations manually - always use the equation_solver tool for equations with variables.
Do NOT do complex calculations manually - always use the calculator tool.
Do NOT recite formulas from memory - always use the formula_lookup tool.

The system will handle the function calling automatically when you call these tools.
"""

        return f"""You are {self.name}.

{self.instruction}

{self.description}{tools_section}

Remember to:
- Use tools IMMEDIATELY when the query requires them (equations → equation_solver, calculations → calculator, formulas → formula_lookup)
- Provide clear, educational explanations AFTER using tools
- Show your reasoning step by step
- Always aim to help the student understand concepts, not just provide answers
""" 