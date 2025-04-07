from typing import List
from fastapi import FastAPI

import models
import core

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World!!!"}


@app.post("/api/v1/calculate/default")
async def calculate_plate(spec: models.ProductionSpecification):
    res, rpr, ret_price = core.calculate_plan(spec)
    return {"result": res, "left_ready_plates": rpr, "retooling_price": ret_price}


@app.post("/api/v1/calculate/optimal-track")
async def calculate_optimal_track_plan(spec: models.ProductionSpecification):
    res = core.calculate_plan_max_fill(spec)
    return res


@app.post("/api/v1/calculate/optimal-cost")
async def calculate_optimal_cost_plan(spec: models.ProductionSpecification):
    res = core.calculate_plan_min_mix(spec)
    return res

@app.post("/api/v1/calculate/optimal-retool")
async def calculate_optimal_retool_plan(spec: models.ProductionSpecification):
    res = core.calculate_plan_min_retooling(spec)
    return res