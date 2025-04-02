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
    res = core.calculate_plan(spec)
    return res


@app.post("/api/v1/calculate/optimal-track")
async def calculate_optimal_track_plan(spec: models.ProductionSpecification):
    res = core.calculate_optimal_for_track_plan(spec)
    return res


@app.post("/api/v1/calculate/optimal-cost")
async def calculate_optimal_cost_plan(spec: models.ProductionSpecification):
    res = core.calculate_optimal_cost_plan(spec)
    return res


