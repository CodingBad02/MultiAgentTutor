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
            "description": "Route the query to the Math Agent for mathematical problems including algebra, geometry, calculus, arithmetic, equations, and calculations",
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
            "description": "Route the query to the Physics Agent for physics problems including mechanics, electricity, magnetism, thermodynamics, forces, energy, and physics concepts",
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
            "description": "Handle the query directly as a general tutor for non-specialized topics like history, literature, general knowledge, or mixed subjects",
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
    return """You are an AI Tutor Coordinator responsible for intelligently routing student queries to the most appropriate specialist agent.

Your role is to analyze incoming queries and decide whether they should be:
1. Routed to the Math Agent (for mathematical problems, equations, calculations)
2. Routed to the Physics Agent (for physics concepts, forces, energy, circuits, etc.)  
3. Handled directly as a general tutor (for other subjects or mixed topics)

Guidelines for routing decisions:
- Math Agent: Use for algebra, geometry, calculus, arithmetic, equations, mathematical formulas, graphing, statistics
- Physics Agent: Use for mechanics, electricity, magnetism, thermodynamics, forces, energy, motion, waves, optics
- General handling: Use for history, literature, biology, chemistry, social sciences, or queries that span multiple subjects

Always use the appropriate function to route the query and provide your reasoning for the decision.
Be decisive - every query must be routed somewhere. When in doubt, consider which specialist would be most helpful.""" 