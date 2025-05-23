# app/agents/physics_agent.py
import re
import time
from typing import List
from .base_agent import BaseAgent, TaskRequest, AgentResponse
from ..tools.calculator_tool import CalculatorTool
from ..tools.formula_lookup_tool import FormulaLookupTool
from ..utils.logger import AgentLogger


class PhysicsAgent(BaseAgent):
    """
    Specialized agent for physics tutoring following Google ADK patterns.
    Handles mechanics, electricity, thermodynamics, and other physics concepts.
    """
    
    def __init__(self):
        super().__init__(
            name="Physics Tutor",
            description="I am a specialized physics tutor with expertise in mechanics, electricity, magnetism, thermodynamics, and modern physics. I can solve physics problems, explain concepts, perform calculations with proper units, and help students understand the fundamental principles of physics.",
            instruction="""You are a specialized Physics Tutor agent. Your primary role is to help students understand and solve physics problems.

Your expertise covers:
- Classical Mechanics (motion, forces, energy, momentum)
- Electricity and Magnetism (circuits, fields, electromagnetic waves)
- Thermodynamics (heat, temperature, entropy, gas laws)
- Waves and Optics (sound, light, interference, diffraction)
- Modern Physics (relativity, quantum mechanics, atomic physics)

When solving physics problems, you SHOULD use the available tools when appropriate:
- Use the "calculator" tool for complex numerical computations involving physics formulas
- Use the "formula_lookup" tool when you need specific physics formulas or constants

When solving physics problems:
1. Identify the relevant physics principles and laws
2. Set up the problem with proper diagrams when helpful
3. Use correct units throughout all calculations
4. Use tools for calculations when needed
5. Explain the physical meaning of results
6. Connect concepts to real-world applications
7. Verify that answers make physical sense

Always emphasize understanding of physical concepts, not just mathematical manipulation."""
        )
        
        # Add physics-specific tools
        self.add_tool(CalculatorTool())
        self.add_tool(FormulaLookupTool())
        
        # Set up logging
        self.agent_logger = AgentLogger("Physics Tutor")
        
        # Keywords for basic confidence scoring
        self.physics_keywords = [
            "physics", "force", "energy", "motion", "velocity", "acceleration", "momentum",
            "newton", "joule", "watt", "electric", "magnetic", "current", "voltage", "resistance",
            "circuit", "ohm", "ampere", "volt", "charge", "field", "wave", "frequency",
            "thermodynamics", "temperature", "heat", "entropy", "pressure", "volume",
            "gravity", "gravitational", "mass", "weight", "friction", "tension", "spring",
            "kinetic", "potential", "mechanical", "electromagnetic", "quantum", "photon",
            "electron", "proton", "atom", "nuclear", "radioactive", "radiation",
            "optics", "lens", "mirror", "refraction", "reflection", "interference",
            "oscillation", "pendulum", "harmonic", "resonance", "doppler"
        ]
        
        self.physics_units = [
            "m/s", "m/s²", "kg", "N", "J", "W", "V", "A", "Ω", "C", "T", "Hz", "K", "°C", "Pa"
        ]
    
    def can_handle(self, query: str) -> float:
        """
        Determine if this agent can handle the physics query.
        This is used as a fallback - primary routing is now done by Gemini.
        """
        query_lower = query.lower()
        
        # Check for physics keywords
        keyword_score = sum(1 for keyword in self.physics_keywords if keyword in query_lower)
        
        # Check for physics units
        unit_score = sum(1 for unit in self.physics_units if unit in query)
        
        # Check for physics-specific patterns
        physics_patterns = [
            r'F\s*=\s*ma',                    # Newton's second law
            r'E\s*=\s*mc²',                   # Einstein's equation
            r'V\s*=\s*IR',                    # Ohm's law
            r'KE\s*=\s*½mv²',                # Kinetic energy
            r'PE\s*=\s*mgh',                 # Potential energy
            r'\d+\s*(m/s|m/s²|kg|N|J|W|V|A)', # Numbers with physics units
        ]
        
        pattern_score = sum(1 for pattern in physics_patterns if re.search(pattern, query))
        
        # Combine scores
        total_score = (keyword_score * 0.4) + (unit_score * 0.3) + (pattern_score * 0.3)
        
        # Normalize to 0-1 range
        max_possible_score = len(self.physics_keywords) * 0.4 + len(self.physics_units) * 0.3 + len(physics_patterns) * 0.3
        confidence = min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
        
        # Boost confidence for clear physics queries
        if any(word in query_lower for word in ["physics", "force", "energy", "electric", "magnetic"]):
            confidence = min(confidence + 0.2, 1.0)
        
        return confidence
    
    def process_task(self, task: TaskRequest) -> AgentResponse:
        """
        Process a physics task using Gemini with function calling for tools.
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
                        sources=["Physics Agent", "Gemini 2.0 Flash"],
                        execution_time_ms=execution_time,
                        metadata={
                            "agent": "Physics Agent",
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
            self.agent_logger.log_agent_complete(execution_time, 0.85)
            
            return AgentResponse(
                content=final_response,
                confidence=0.85,  # High confidence for physics problems
                sources=["Physics Agent", "Gemini 2.0 Flash"],
                execution_time_ms=execution_time,
                metadata={
                    "agent": "Physics Agent",
                    "tools_available": self.get_available_tools(),
                    "system_prompt": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.agent_logger.log_error(e, "processing physics task")
            
            return AgentResponse(
                content=f"I encountered an error while processing your physics question: {str(e)}. Please try rephrasing your question.",
                confidence=0.1,
                execution_time_ms=execution_time,
                metadata={"error": str(e), "agent": "Physics Agent"}
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
        
        # Combine all parts and send back through Gemini for final formatting
        raw_response = "\n".join(response_parts)
        self.agent_logger.logger.info(f"🔄 Function calls made: {len(function_calls_made)}")
        
        # Send the response back through Gemini for better formatting and explanation
        formatting_prompt = f"""Please format and explain this physics solution clearly for a student:

Original Question: {task.query}

Solution Process: {raw_response}

Tool Results Used: {function_calls_made}

Please provide a clear, step-by-step explanation that:
1. Identifies the relevant physics principles
2. Shows all calculations with proper units
3. Explains the physical meaning of the result
4. Helps the student understand the underlying concepts
5. Mentions what tools were used and why"""

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
- For formula requests (like "what is the formula for kinetic energy"), immediately call formula_lookup
- For complex numerical calculations with physics formulas, immediately call calculator
- For any computation involving multiple steps or special functions, immediately call calculator

Do NOT recite formulas from memory - always use the formula_lookup tool to get accurate formulas.
Do NOT do complex calculations manually - always use the calculator tool.

The system will handle the function calling automatically when you call these tools.
"""

        return f"""You are {self.name}.

{self.instruction}

{self.description}{tools_section}

Remember to:
- Use tools IMMEDIATELY when the query requires them (formulas → formula_lookup, calculations → calculator)
- Provide clear, educational explanations AFTER using tools
- Show your reasoning step by step with proper physics principles
- Always use correct units and verify physical reasonableness
- Always aim to help the student understand concepts, not just provide answers
""" 