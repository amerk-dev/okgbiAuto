from fastapi import APIRouter
from core import (
    calculate_plan,
    calculate_plan_max_fill,
    calculate_plan_min_mix,
    calculate_plan_min_retooling
)
from models import ProductionSpecification

v1_router = APIRouter(prefix="/v1", tags=["v1"])


@v1_router.post("/calculate/default")
async def calculate_plate(spec: ProductionSpecification):
    res, used_ready_plates, unplaced_plates_merged, updated_ready_plates, ret_price, is_real = calculate_plan(spec)
    if is_real:
        return {
            "plan": res,
            "used_ready_plates": used_ready_plates,
            "unplaced_plates": unplaced_plates_merged,
            "left_ready_plates": updated_ready_plates,
            "retooling_info": ret_price,
        }
    else:
        return {
            "Message": "Невозможно распределить все плиты, не хватает дорожек",
            "plan": res,
            "used_ready_plates": used_ready_plates,
            "unplaced_plates": unplaced_plates_merged,
            "left_ready_plates": updated_ready_plates,
            "retooling_info": ret_price,
        }




@v1_router.post("/calculate/optimal-track")
async def calculate_optimal_track_plan(spec: ProductionSpecification):
    res, used_ready_plates, unplaced_plates_merged, updated_ready_plates, ret_price, is_real = calculate_plan_max_fill(spec)
    if is_real:
        return {
            "plan": res,
            "used_ready_plates": used_ready_plates,
            "unplaced_plates": unplaced_plates_merged,
            "left_ready_plates": updated_ready_plates,
            "retooling_info": ret_price,
        }
    else:
        return {
            "Message": "Невозможно распределить все плиты, не хватает дорожек",
            "plan": res,
            "used_ready_plates": used_ready_plates,
            "unplaced_plates": unplaced_plates_merged,
            "left_ready_plates": updated_ready_plates,
            "retooling_info": ret_price,
        }


@v1_router.post("/calculate/optimal-cost")
async def calculate_optimal_cost_plan(spec: ProductionSpecification):
    res, used_ready_plates, unplaced_plates_merged, updated_ready_plates, ret_price, is_real = calculate_plan_min_mix(spec)
    if is_real:
        return {
            "plan": res,
            "used_ready_plates": used_ready_plates,
            "unplaced_plates": unplaced_plates_merged,
            "left_ready_plates": updated_ready_plates,
            "retooling_info": ret_price,
        }
    else:
        return {
            "Message": "Невозможно распределить все плиты, не хватает дорожек",
            "plan": res,
            "used_ready_plates": used_ready_plates,
            "unplaced_plates": unplaced_plates_merged,
            "left_ready_plates": updated_ready_plates,
            "retooling_info": ret_price,
        }


@v1_router.post("/calculate/optimal-retool")
async def calculate_optimal_retool_plan(spec: ProductionSpecification):
    res, used_ready_plates, unplaced_plates_merged, updated_ready_plates, ret_price, is_real = calculate_plan_min_retooling(spec)
    if is_real:
        return {
            "plan": res,
            "used_ready_plates": used_ready_plates,
            "unplaced_plates": unplaced_plates_merged,
            "left_ready_plates": updated_ready_plates,
            "retooling_info": ret_price,
        }
    else:
        return {
            "Message": "Невозможно распределить все плиты, не хватает дорожек",
            "plan": res,
            "used_ready_plates": used_ready_plates,
            "unplaced_plates": unplaced_plates_merged,
            "left_ready_plates": updated_ready_plates,
            "retooling_info": ret_price,
        }
