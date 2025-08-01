from typing import Dict, Any
from .calculator import PlanCalculator


def calculate_plan() -> Dict[str, Any]:
    """
    Backward compatibility function that uses the new PlanCalculator class.

    Returns:
        Dict[str, Any]: The calculation result containing the plan and statistics.
    """
    calculator = PlanCalculator()
    return calculator.calculate_plan()
