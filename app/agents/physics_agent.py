# app/agents/physics_agent.py
import re
import time
from typing import List
from .base_agent import BaseAgent, TaskRequest, AgentResponse
from ..utils.logger import AgentLogger


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
Focus on education and understanding of physical principles."""
        )
        
        self.agent_logger = AgentLogger("Physics Tutor")
        
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
    
    def process_task(self, task: TaskRequest) -> AgentResponse:
        """
        Process a physics task by directly using the Gemini model.
        """
        start_time = time.time()
        self.agent_logger.log_agent_start(task.query)
        
        try:
            system_prompt = self.get_system_prompt()
            user_prompt = self._prepare_prompt_with_context(task)
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            self.agent_logger.log_gemini_request(full_prompt)
            
            response = self.model.generate_content(full_prompt)
            final_response = response.text
            
            self.agent_logger.log_gemini_response(final_response)
            
            execution_time = (time.time() - start_time) * 1000
            self.agent_logger.log_agent_complete(execution_time, 0.85) 
            
            return AgentResponse(
                content=final_response,
                confidence=0.85, 
                sources=["Physics Tutor", "Gemini 2.0 Flash"],
                execution_time_ms=execution_time,
                metadata={
                    "agent": "Physics Tutor",
                    "system_prompt_preview": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.agent_logger.log_error(e, "processing physics task")
            
            return AgentResponse(
                content=f"I encountered an error while trying to help with your physics question: {str(e)}. Please try rephrasing.",
                confidence=0.1,
                execution_time_ms=execution_time,
                metadata={"error": str(e), "agent": "Physics Tutor"}
            )

    # Removed _process_function_calls method
    # System prompt is now inherited from BaseAgent or can be overridden if needed
    
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