# app/agents/physics_agent.py
import re
import time
from typing import List, Dict, Any
from .base_agent import BaseAgent, TaskRequest, AgentResponse
from ..utils.logger import AgentLogger
from ..tools.calculator_tool import CalculatorTool
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
            description="I am a specialized physics tutor with expertise in mechanics, electricity, magnetism, thermodynamics, and modern physics. I can explain physics concepts, and help students understand the fundamental principles of physics.",
            instruction="""You are a specialized Physics Tutor agent. Your primary role is to help students understand physics problems and concepts.

Your expertise covers:
- Classical Mechanics (motion, forces, energy, momentum)
- Electricity and Magnetism (circuits, fields, electromagnetic waves)
- Thermodynamics (heat, temperature, entropy, gas laws)
- Waves and Optics (sound, light, interference, diffraction)
- Modern Physics (relativity, quantum mechanics, atomic physics)

Explain concepts clearly and provide step-by-step solutions where appropriate.
Focus on education and understanding of physical principles.

You have access to tools that can help with calculations and formula lookups. Use these tools when appropriate to provide accurate answers."""
        )
        
        self.agent_logger = AgentLogger("Physics Tutor")
        
        # Initialize tools
        self.calculator = CalculatorTool() if 'CalculatorTool' in globals() else None
        self.formula_lookup = FormulaLookupTool()
        
        # Register tools
        self.tools = []
        if self.formula_lookup:
            self.tools.append(self.formula_lookup)
        if self.calculator:
            self.tools.append(self.calculator)
        
        # Store tool information for logging and runtime use
        self.function_declarations = []
        for tool in self.tools:
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
                self.function_declarations.append({
                    "name": tool.name,
                    "description": tool.description
                })
        
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
        """
        query_lower = query.lower()
        keyword_score = sum(1 for keyword in self.physics_keywords if keyword in query_lower)
        unit_score = sum(1 for unit in self.physics_units if unit in query)
        physics_patterns = [
            r'F\s*=\s*ma',
            r'E\s*=\s*mc²',
            r'V\s*=\s*IR',
            r'KE\s*=\s*½mv²',
            r'PE\s*=\s*mgh',
            r'\d+\s*(m/s|m/s²|kg|N|J|W|V|A)',
        ]
        pattern_score = sum(1 for pattern in physics_patterns if re.search(pattern, query))
        total_score = (keyword_score * 0.4) + (unit_score * 0.3) + (pattern_score * 0.3)
        max_possible_score = len(self.physics_keywords) * 0.4 + len(self.physics_units) * 0.3 + len(physics_patterns) * 0.3
        confidence = min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
        if any(word in query_lower for word in ["physics", "force", "energy", "electric", "magnetic"]):
            confidence = min(confidence + 0.2, 1.0)
        return confidence
    
    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool names.
        """
        return [tool.name for tool in self.tools]
    
    def process_task(self, task: TaskRequest) -> AgentResponse:
        """
        Process a physics task using manual tool detection for serverless compatibility.
        """
        start_time = time.time()
        self.agent_logger.log_agent_start(task.query)
        flow_id = self.agent_logger.flow_id
        
        try:
            # Add tool information to the system prompt if we have tools
            tools_info = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools]) if self.tools else ""
            system_prompt = self.get_system_prompt()
            if tools_info:
                system_prompt = f"{system_prompt}\n\nAvailable tools:\n{tools_info}"
                
            user_prompt = self._prepare_prompt_with_context(task)
            
            # Log available tools
            if self.function_declarations:
                tool_names = [func_decl["name"] for func_decl in self.function_declarations]
                self.agent_logger.log_tool_schemas([{"name": name} for name in tool_names])
            
            self.agent_logger.log_gemini_request(user_prompt)
            
            # For deployment compatibility, detect if we need a tool
            needs_formula_lookup = any(x in task.query.lower() for x in ["formula", "equation for", "what is the formula"])
            needs_calculator = any(x in task.query.lower() for x in ["calculate", "compute", "find the value", "solve for"])
            
            # Call appropriate tool directly if needed
            tool_result = None
            tool_name = None
            tool_args = {}
            
            if needs_formula_lookup and self.formula_lookup:
                tool_name = "formula_lookup"
                # Extract the formula name from the query
                formula_query = task.query.lower()
                
                # Detect specific physics formulas
                if "kinetic energy" in formula_query:
                    query = "kinetic_energy"
                elif "potential energy" in formula_query:
                    query = "potential_energy"
                elif "force" in formula_query and ("newton" in formula_query or "second law" in formula_query):
                    query = "force"
                elif "ohm" in formula_query or "voltage" in formula_query:
                    query = "ohms_law"
                else:
                    # Just pass the whole query if we can't identify a specific formula
                    query = formula_query
                
                tool_args = {"query": query}
                tool_result = self._execute_tool(tool_name, tool_args)
            
            # If we used a tool, process the result
            if tool_result and tool_result.success:
                final_response = self._process_tool_result(task.query, tool_name, tool_args, tool_result)
                used_tools = [tool_name]
                self.agent_logger.log_tool_call(tool_name, tool_args, tool_result.result)
            else:
                # Otherwise, use the model normally
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = self.model.generate_content(full_prompt)
                final_response = response.text
                used_tools = []
            
            self.agent_logger.log_gemini_response(final_response)
            
            execution_time = (time.time() - start_time) * 1000
            self.agent_logger.log_agent_complete(execution_time, 0.85)
            
            # Create metadata
            metadata = {
                "agent": "Physics Tutor",
                "flow_id": flow_id,
                "tools_available": self.get_available_tools(),
                "tools_used": used_tools,
                "tool_calls_count": len(used_tools)
            }
            
            return AgentResponse(
                content=final_response,
                confidence=0.85, 
                sources=["Physics Tutor", "Gemini 2.0 Flash"] + used_tools,
                execution_time_ms=execution_time,
                metadata=metadata
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
    
    def _process_tool_result(self, query: str, tool_name: str, tool_args: Dict[str, Any], tool_result: ToolResult) -> str:
        """
        Process the tool result with the model to generate a final response.
        """
        # Format the result in a readable way
        result_str = str(tool_result.result)
        if isinstance(tool_result.result, dict):
            try:
                result_str = "\n".join([f"{k}: {v}" for k, v in tool_result.result.items()])
            except:
                pass
        
        # Prepare prompt for processing the tool result
        tool_output_prompt = f"""
You are a Physics Tutor helping a student with the question: "{query}".

To solve this problem, you used the tool "{tool_name}" 
with arguments: {tool_args}

The tool returned this result: {result_str}

Based on this tool result, please provide a complete educational response that:
1. Explains what the tool did
2. Explains the physics concepts involved
3. Shows how this applies to the student's question
4. Concludes with the final answer

Your goal is to help the student understand the underlying physics principles.
"""
        
        # Process the tool result with the model
        try:
            result_response = self.model.generate_content(tool_output_prompt)
            return result_response.text
        except Exception as e:
            # Fallback if there's an error
            return f"I found the answer to your physics question using my {tool_name}. The result is: {result_str}. Let me know if you need further explanation!"
    
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