# app/tools/formula_lookup_tool.py
from typing import Any, Dict, List
from .base_tool import BaseTool, ToolResult


class FormulaLookupTool(BaseTool):
    """
    A tool for looking up common mathematical and physics formulas.
    """
    
    def __init__(self):
        super().__init__(
            name="formula_lookup",
            description="Look up common mathematical and physics formulas by name or concept"
        )
        
        self.formulas = {
            # Math formulas
            "quadratic_formula": {
                "formula": "x = (-b ± √(b² - 4ac)) / (2a)",
                "description": "Solve quadratic equations of the form ax² + bx + c = 0",
                "variables": {"a": "coefficient of x²", "b": "coefficient of x", "c": "constant term"}
            },
            "area_circle": {
                "formula": "A = πr²",
                "description": "Area of a circle",
                "variables": {"A": "area", "r": "radius", "π": "pi (≈3.14159)"}
            },
            "area_triangle": {
                "formula": "A = ½bh",
                "description": "Area of a triangle",
                "variables": {"A": "area", "b": "base", "h": "height"}
            },
            "pythagorean_theorem": {
                "formula": "a² + b² = c²",
                "description": "Relationship between sides of a right triangle",
                "variables": {"a": "first leg", "b": "second leg", "c": "hypotenuse"}
            },
            
            # Physics formulas
            "kinematic_position": {
                "formula": "x = x₀ + v₀t + ½at²",
                "description": "Position as a function of time with constant acceleration",
                "variables": {"x": "final position", "x₀": "initial position", "v₀": "initial velocity", "t": "time", "a": "acceleration"}
            },
            "kinematic_velocity": {
                "formula": "v = v₀ + at",
                "description": "Velocity as a function of time with constant acceleration",
                "variables": {"v": "final velocity", "v₀": "initial velocity", "a": "acceleration", "t": "time"}
            },
            "force": {
                "formula": "F = ma",
                "description": "Newton's second law of motion",
                "variables": {"F": "force (N)", "m": "mass (kg)", "a": "acceleration (m/s²)"}
            },
            "kinetic_energy": {
                "formula": "KE = ½mv²",
                "description": "Kinetic energy of a moving object",
                "variables": {"KE": "kinetic energy (J)", "m": "mass (kg)", "v": "velocity (m/s)"}
            },
            "potential_energy": {
                "formula": "PE = mgh",
                "description": "Gravitational potential energy",
                "variables": {"PE": "potential energy (J)", "m": "mass (kg)", "g": "acceleration due to gravity (9.8 m/s²)", "h": "height (m)"}
            },
            "ohms_law": {
                "formula": "V = IR",
                "description": "Relationship between voltage, current, and resistance",
                "variables": {"V": "voltage (V)", "I": "current (A)", "R": "resistance (Ω)"}
            }
        }
    
    def execute(self, query: str) -> ToolResult:
        """
        Look up a formula based on the query.
        """
        try:
            query = query.lower().strip()
            
            # Direct lookup
            if query in self.formulas:
                formula_data = self.formulas[query]
                return ToolResult(
                    success=True,
                    result=formula_data,
                    metadata={"query": query, "lookup_type": "direct"}
                )
            
            # Fuzzy search
            matches = self._fuzzy_search(query)
            
            if matches:
                if len(matches) == 1:
                    formula_data = self.formulas[matches[0]]
                    return ToolResult(
                        success=True,
                        result=formula_data,
                        metadata={"query": query, "lookup_type": "fuzzy", "matched_key": matches[0]}
                    )
                else:
                    # Multiple matches
                    return ToolResult(
                        success=True,
                        result={
                            "multiple_matches": True,
                            "suggestions": [
                                {"key": key, "description": self.formulas[key]["description"]}
                                for key in matches
                            ]
                        },
                        metadata={"query": query, "lookup_type": "multiple_matches"}
                    )
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"No formula found for '{query}'. Try keywords like 'quadratic', 'circle', 'force', 'energy', etc."
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Lookup error: {str(e)}"
            )
    
    def _fuzzy_search(self, query: str) -> List[str]:
        """
        Search for formulas that match the query keywords.
        """
        matches = []
        query_words = query.split()
        
        for key, data in self.formulas.items():
            # Check if query words appear in key or description
            search_text = f"{key} {data['description']}".lower()
            
            if any(word in search_text for word in query_words):
                matches.append(key)
        
        return matches
    
    def get_all_formulas(self) -> Dict[str, Any]:
        """
        Get all available formulas.
        """
        return self.formulas
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Formula name or concept to look up (e.g., 'quadratic formula', 'area of circle', 'force', 'kinetic energy')"
                }
            },
            "required": ["query"]
        } 