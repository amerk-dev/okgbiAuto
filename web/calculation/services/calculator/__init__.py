"""
Calculator module for calculating plans.
"""
from .calculator import PlanCalculator
from .middleware import (
    Middleware,
    MiddlewareContext,
    InitialPlacementMiddleware,
    ConcreteClassOptimizationMiddleware,
    WireOptimizationMiddleware,
)
from .utils import (
    profile_time,
    get_parameters,
    swap_plates,
    reality_check,
    add_plate_to_track,
)

# For backward compatibility
from .calculate import calculate_plan

__all__ = [
    'PlanCalculator',
    'calculate_plan',
    'Middleware',
    'MiddlewareContext',
    'InitialPlacementMiddleware',
    'ConcreteClassOptimizationMiddleware',
    'WireOptimizationMiddleware',
    'profile_time',
    'get_parameters',
    'swap_plates',
    'reality_check',
    'add_plate_to_track',
]
