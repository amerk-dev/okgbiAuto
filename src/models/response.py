from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field
from .request import PlateSpecification

class TrackConfig(BaseModel):
    day: date
    height: int
    width: int
    useful_len: int
    free_len: int
    concrete_class: str
    wire_bottom: int
    wire_top: int
    total_cost: float
    plates: List[PlateSpecification] = Field(default_factory=list)