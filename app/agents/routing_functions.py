"""
Function declarations for dynamic agent routing using Gemini's function calling.
Following Google ADK patterns for multi-agent delegation.
"""

from typing import Dict, Any, List

def get_routing_function_declarations() -> List[Dict[str, Any]]:
    """
    Return function declarations for agent routing that Gemini can use
    to dynamically decide which specialist agent should handle a query.
    """
    return [
        {
            "name": "route_to_math_agent",
            "description": "Route the query to the Math Agent for mathematical problems including algebra, geometry, calculus, arithmetic, and general math questions. The Math Agent will provide explanations and solutions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The mathematical query to be handled by the Math Agent"
                    },
                    "reasoning": {
                        "type": "string", 
                        "description": "Brief explanation of why this should be routed to the Math Agent"
                    }
                },
                "required": ["query", "reasoning"]
            }
        },
        {
            "name": "route_to_physics_agent", 
            "description": "Route the query to the Physics Agent for physics problems including mechanics, electricity, magnetism, thermodynamics, forces, energy, and general physics concepts. The Physics Agent will provide explanations and insights.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The physics query to be handled by the Physics Agent"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why this should be routed to the Physics Agent"  
                    }
                },
                "required": ["query", "reasoning"]
            }
        },
        {
            "name": "handle_general_query",
            "description": "Handle the query directly as a general tutor for non-specialized topics like history, literature, general knowledge, or mixed subjects. The general tutor will provide a comprehensive answer.",
            "parameters": {
                "type": "object", 
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The general query to be handled directly"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why this is being handled as a general query"
                    }
                },
                "required": ["query", "reasoning"]
            }
        }
    ]

def get_routing_system_prompt() -> str:
    """
    Get the system prompt for the routing decision.
    This prompt guides Gemini in making intelligent routing decisions.
    """
    return """You are an AI Tutor Coordinator responsible for intelligently routing student queries to the most appropriate specialist agent or handling them directly.

Your role is to analyze incoming queries and decide whether they should be:
1. Routed to the Math Agent (for mathematical problems, equations, concepts)
2. Routed to the Physics Agent (for physics concepts, principles, problems)  
3. Handled directly as a general tutor (for other subjects or mixed topics)

Guidelines for routing decisions:
- Math Agent: Use for questions related to algebra, geometry, calculus, arithmetic, mathematical concepts. The Math Agent will explain and help solve these.
- Physics Agent: Use for questions related to mechanics, electricity, magnetism, thermodynamics, forces, energy, motion, waves, optics, and other physics topics. The Physics Agent will explain these concepts.
- Biology Agent: Use for questions related to biology concepts, principles, problems. The Biology Agent will explain these concepts.
- General handling: Use for history, literature, biology, chemistry, social sciences, or queries that span multiple subjects, or if unsure. The general tutor will provide an answer.

Always use the appropriate function to route the query and provide your reasoning for the decision.
Be decisive - every query must be routed. When in doubt about specialization, opt for general handling.""" 