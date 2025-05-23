# app/tools/calculator_tool.py
import math
import re
from typing import Any, Dict
from .base_tool import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    """
    A calculator tool for basic mathematical operations.
    """
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform basic mathematical calculations including arithmetic, trigonometry, and logarithms"
        )
    
    def execute(self, expression: str) -> ToolResult:
        """
        Execute a mathematical expression safely.
        """
        try:
            # Clean the expression
            expression = expression.strip()
            
            # Replace common math functions
            expression = self._prepare_expression(expression)
            
            # Evaluate safely
            allowed_names = {
                k: v for k, v in math.__dict__.items() if not k.startswith("__")
            }
            allowed_names.update({"abs": abs, "round": round})
            
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            
            return ToolResult(
                success=True,
                result=result,
                metadata={"expression": expression}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Calculation error: {str(e)}"
            )
    
    def _prepare_expression(self, expr: str) -> str:
        """
        Prepare expression for safe evaluation.
        """
        # Replace common mathematical notation
        replacements = {
            r'\^': '**',  # Replace ^ with **
            r'ln\(': 'log(',  # Natural log
            r'log10\(': 'log10(',  # Base 10 log
            r'√\(': 'sqrt(',  # Square root
        }
        
        for pattern, replacement in replacements.items():
            expr = re.sub(pattern, replacement, expr)
        
        return expr
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 3 * sin(pi/4)')"
                }
            },
            "required": ["expression"]
        } 