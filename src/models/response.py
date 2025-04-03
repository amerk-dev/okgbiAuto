from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field
from .request import PlateSpecification

class TrackConfig(BaseModel):
    day: date
    height: int
    width: int
    free_len: int
    plates: List[PlateSpecification] = Field(default_factory=list)