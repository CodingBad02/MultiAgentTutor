# app/agents/tutor_agent.py
import time
from typing import Optional, Dict, Any
from .base_agent import BaseAgent, TaskRequest, AgentResponse
from .agent_registry import AgentRegistry
from .routing_functions import get_routing_function_declarations, get_routing_system_prompt
from ..utils.logger import AgentLogger
import google.generativeai as genai
import google.generativeai.types as gapic_types


class TutorAgent(BaseAgent):
    """
    Main orchestrator agent that uses Gemini's function calling for dynamic routing.
    Follows Google ADK principles for multi-agent coordination and delegation.
    """
    
    def __init__(self):
        super().__init__(
            name="AI Tutor Coordinator",
            description="I am your intelligent AI tutor coordinator. I analyze your questions and dynamically route them to the most appropriate specialist tutor or handle them myself.",
            instruction=get_routing_system_prompt()
        )
        
        self.registry = AgentRegistry()
        # Use the same model for routing decisions
        self.routing_model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Set up logging
        self.agent_logger = AgentLogger("AI Tutor Coordinator")
    
    def can_handle(self, query: str) -> float:
        """
        The tutor agent can handle any query with high confidence since it can route dynamically.
        """
        return 0.95  # Always high confidence since we can route or handle directly
    
    def process_task(self, task: TaskRequest) -> AgentResponse:
        """
        Process a task by routing to a specialist or handling directly.
        """
        start_time = time.time()
        
        # Log agent start
        self.agent_logger.log_agent_start(task.query)
        
        try:
            # Step 1: Use Gemini with function calling to decide routing
            self.agent_logger.logger.info("🎯 Starting routing decision process...")
            routing_decision = self._make_routing_decision(task)
            
            # Log the routing decision
            self.agent_logger.log_routing_decision(task.query, routing_decision)
            
            if routing_decision["action"] == "delegate":
                # Step 2: Delegate to specialist agent
                self.agent_logger.log_delegation(
                    "AI Tutor Coordinator", 
                    routing_decision["agent_name"], 
                    routing_decision["reasoning"]
                )
                
                specialist_response = self._delegate_to_specialist(
                    routing_decision["agent_key"], 
                    task,
                    routing_decision["reasoning"]
                )
                
                # Directly return specialist response without enhancement
                return specialist_response
                
            else:
                # Step 2: Handle directly as general tutor
                self.agent_logger.logger.info("📚 Handling query directly as general tutor")
                return self._handle_general_query(task, routing_decision["reasoning"], start_time)
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.agent_logger.log_error(e, "processing task")
            
            return AgentResponse(
                content=f"I encountered an error while processing your request: {str(e)}. Please try rephrasing your question.",
                confidence=0.1,
                execution_time_ms=execution_time,
                metadata={"error": str(e), "agent": "AI Tutor Coordinator"}
            )
    
    def _make_routing_decision(self, task: TaskRequest) -> Dict[str, Any]:
        """
        Use Gemini with function calling to make intelligent routing decisions.
        This is the core ADK pattern - let the LLM decide delegation dynamically.
        """
        try:
            # Get function declarations for routing
            routing_functions = get_routing_function_declarations()
            self.agent_logger.logger.info(f"🔧 Using {len(routing_functions)} routing functions for TutorAgent decision")
            
            # Create the routing prompt
            routing_prompt = f"""Analyze this student query and decide how to handle it:

Student Query: "{task.query}"

Context: {task.context if task.context else "None provided"}

Use the appropriate function to route this query. Consider:
- Subject matter (Math, Physics, or General)
- Student's likely learning needs

Be decisive. Choose 'route_to_math_agent' for math, 'route_to_physics_agent' for physics, or 'handle_general_query' for others."""

            self.agent_logger.log_gemini_request(routing_prompt)
            
            # Use Gemini with function calling to make the decision
            # Create tools configuration using explicit types
            function_declarations_typed = [gapic_types.FunctionDeclaration(**schema) for schema in routing_functions]
            # Ensure we only create a Tool if there are declarations
            tools_list = [gapic_types.Tool(function_declarations=function_declarations_typed)] if function_declarations_typed else []

            response = self.routing_model.generate_content(
                routing_prompt,
                tools=tools_list
            )
            
            self.agent_logger.logger.info(f"📋 Routing response candidates: {len(response.candidates) if response.candidates else 0}")
            
            # Parse the function call response
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        func_call = part.function_call
                        func_name = func_call.name
                        func_args = dict(func_call.args)
                        
                        self.agent_logger.log_function_call_detected(func_name, func_args)
                        
                        if func_name == "route_to_math_agent":
                            return {
                                "action": "delegate",
                                "agent_key": "math", 
                                "agent_name": "Math Tutor",
                                "reasoning": func_args.get("reasoning", "Math-related query"),
                                "query": func_args.get("query", task.query)
                            }
                        elif func_name == "route_to_physics_agent":
                            return {
                                "action": "delegate",
                                "agent_key": "physics",
                                "agent_name": "Physics Tutor", 
                                "reasoning": func_args.get("reasoning", "Physics-related query"),
                                "query": func_args.get("query", task.query)
                            }
                        elif func_name == "handle_general_query":
                            return {
                                "action": "handle_directly",
                                "reasoning": func_args.get("reasoning", "General knowledge query"),
                                "query": func_args.get("query", task.query)
                            }
            
            # Fallback if no function call was made
            self.agent_logger.logger.warning("⚠️ No function call detected in routing response. Defaulting to general handling.")
            return {
                "action": "handle_directly",
                "reasoning": "No clear specialization identified via function call.",
                "query": task.query
            }
            
        except Exception as e:
            self.agent_logger.log_error(e, "making routing decision")
            
            # Simplified fallback logic
            query_lower = task.query.lower()
            if any(word in query_lower for word in ["math", "equation", "algebra", "calculate"]):
                return {
                    "action": "delegate",
                    "agent_key": "math",
                    "agent_name": "Math Tutor",
                    "reasoning": f"Fallback (error: {str(e)}) - math keywords detected.",
                    "query": task.query
                }
            elif any(word in query_lower for word in ["physics", "force", "energy", "motion"]):
                return {
                    "action": "delegate", 
                    "agent_key": "physics",
                    "agent_name": "Physics Tutor",
                    "reasoning": f"Fallback (error: {str(e)}) - physics keywords detected.",
                    "query": task.query
                }
            else:
                return {
                    "action": "handle_directly",
                    "reasoning": f"Fallback (error: {str(e)}) - no specific keywords.",
                    "query": task.query
                }
    
    def _delegate_to_specialist(self, agent_key: str, task: TaskRequest, reasoning: str) -> AgentResponse:
        """
        Delegate the task to the specified specialist agent.
        """
        agent = self.registry.get_agent(agent_key)
        if not agent:
            self.agent_logger.log_error(ValueError(f"Agent '{agent_key}' not found"), "delegating to specialist")
            return AgentResponse(content=f"Sorry, I couldn't find the right specialist ({agent_key}) for your query.", confidence=0.1)
        
        self.agent_logger.logger.info(f"🚀 Delegating to {agent.name} for: {task.query}")
        
        # Process the task with the specialist
        specialist_response = agent.process_task(task)
        
        self.agent_logger.logger.info(f"✅ Received response from {agent.name} (confidence: {specialist_response.confidence:.2f})")
        
        return specialist_response
    
    def _handle_general_query(self, task: TaskRequest, reasoning: str, start_time: float) -> AgentResponse:
        """
        Handle queries directly as a general tutor using Gemini.
        """
        general_tutor_prompt = f"""You are an AI Tutor Coordinator. 
Student Question: {task.query}
Context: {task.context if task.context else "None provided"}
Routing Decision: You've decided to handle this query directly. Reasoning: {reasoning}
Available Specialists (for future reference by the user, not for you to use now): Math Tutor, Physics Tutor.

Provide a comprehensive, educational response directly to the student."""
        try:
            self.agent_logger.log_gemini_request(general_tutor_prompt)
            response = self.routing_model.generate_content(general_tutor_prompt)
            content = response.text
            self.agent_logger.log_gemini_response(content)
        except Exception as e:
            self.agent_logger.log_error(e, "handling general query")
            content = f"I'd be happy to help with your question: {task.query}. However, I encountered a technical issue while preparing your answer. Could you please rephrase your question?"
        
        execution_time = (time.time() - start_time) * 1000
        
        # Log completion
        self.agent_logger.log_agent_complete(execution_time, 0.7)
        
        return AgentResponse(
            content=content,
            confidence=0.7,
            sources=["AI Tutor Coordinator", "Gemini 2.0 Flash"],
            execution_time_ms=execution_time,
            metadata={
                "agent": "AI Tutor Coordinator",
                "mode": "general_tutor",
                "routing_reasoning": reasoning
            }
        )
    
    def get_available_specialists(self) -> dict:
        """
        Get information about available specialist agents.
        """
        return self.registry.get_agent_capabilities() if hasattr(self.registry, 'get_agent_capabilities') else {agent_key: agent.description for agent_key, agent in self.registry.agents.items()}
    
    def get_routing_info(self, query: str) -> dict:
        """
        Get information about how a query would be routed (for debugging).
        """
        try:
            test_task = TaskRequest(query=query)
            routing_decision = self._make_routing_decision(test_task)
            
            return {
                "query": query,
                "routing_decision": routing_decision,
                "would_delegate": routing_decision["action"] == "delegate",
                "target_agent": routing_decision.get("agent_key"),
                "reasoning": routing_decision["reasoning"]
            }
        except Exception as e:
            return {
                "query": query,
                "error": str(e),
                "routing_decision": "failed"
            } 