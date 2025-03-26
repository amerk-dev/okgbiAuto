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


@app.post("/api/v1/calculate/optimal")
async def calculate_optimal_plan(spec: models.ProductionSpecification):
    res = core.calculate_optimal_plan(spec)
    return res
