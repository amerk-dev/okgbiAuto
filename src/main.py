from typing import List
from fastapi import FastAPI

import models
import core

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World!!!"}


@app.post("/api/v1/calculate/")
async def calculate_plate(spec: models.ProductionSpecification):
    res = core.calculate_plan(spec)
    print(res)
    return res


