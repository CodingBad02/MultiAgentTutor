# app/tools/equation_solver_tool.py
import re
from typing import Any, Dict, List
from .base_tool import BaseTool, ToolResult


class EquationSolverTool(BaseTool):
    """
    A tool for solving simple algebraic equations.
    """
    
    def __init__(self):
        super().__init__(
            name="equation_solver",
            description="Solve simple algebraic equations like 'x + 5 = 10' or '2x - 3 = 7'"
        )
    
    def execute(self, equation: str) -> ToolResult:
        """
        Solve a simple algebraic equation.
        """
        try:
            # Clean the equation
            equation = equation.strip().replace(" ", "")
            
            # Split by equals sign
            if "=" not in equation:
                return ToolResult(
                    success=False,
                    result=None,
                    error="Equation must contain an equals sign"
                )
            
            left, right = equation.split("=")
            
            # Try to solve for x
            solutions = self._solve_linear_equation(left, right)
            
            if solutions:
                return ToolResult(
                    success=True,
                    result=solutions,
                    metadata={"equation": equation, "variable": "x"}
                )
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error="Could not solve this equation"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Solver error: {str(e)}"
            )
    
    def _solve_linear_equation(self, left: str, right: str) -> List[float]:
        """
        Solve simple linear equations of the form ax + b = c
        """
        try:
            # Parse left side (ax + b)
            left_coeff, left_const = self._parse_expression(left)
            
            # Parse right side
            right_coeff, right_const = self._parse_expression(right)
            
            # Rearrange to standard form: (left_coeff - right_coeff)x = (right_const - left_const)
            a = left_coeff - right_coeff
            b = right_const - left_const
            
            if abs(a) < 1e-10:  # Coefficient of x is effectively zero
                if abs(b) < 1e-10:
                    return ["infinite_solutions"]  # 0 = 0, infinite solutions
                else:
                    return []  # 0 = non-zero, no solution
            
            x = b / a
            return [round(x, 6)]
            
        except Exception:
            return []
    
    def _parse_expression(self, expr: str) -> tuple:
        """
        Parse an expression like '2x+3' and return (coefficient_of_x, constant)
        """
        expr = expr.replace("-", "+-")  # Handle negative signs
        
        coeff = 0
        const = 0
        
        # Split by + and process each term
        terms = [term for term in expr.split("+") if term]
        
        for term in terms:
            if 'x' in term:
                # Extract coefficient of x
                x_coeff = term.replace('x', '')
                if x_coeff == '' or x_coeff == '+':
                    coeff += 1
                elif x_coeff == '-':
                    coeff -= 1
                else:
                    coeff += float(x_coeff)
            else:
                # Constant term
                if term:
                    const += float(term)
        
        return coeff, const
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "equation": {
                    "type": "string",
                    "description": "Algebraic equation to solve (e.g., '2x + 3 = 7' or 'x - 5 = 10')"
                }
            },
            "required": ["equation"]
        } 