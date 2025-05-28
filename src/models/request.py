from datetime import date
from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator


class ConcreteClass(BaseModel):
    name: str
    price: float


class WireConfig(BaseModel):
    price: float


class RetoolingConfig(BaseModel):
    price: float


class ProductionTrack(BaseModel):
    length: int


class Directory(BaseModel):
    concrete_classes: List[ConcreteClass] = Field(default_factory=list)
    wire: WireConfig
    retooling: RetoolingConfig
    track: ProductionTrack


class PlateSpecification(BaseModel):
    name: str
    count: int
    length: int
    width: int
    height: int
    order: Optional[str] = None
    concrete_class: str = Field(alias="class")
    wire_bottom: int
    wire_top: int

    class Config:
        allow_population_by_field_name = True


class AvailableTrack(BaseModel):
    count: int
    day: date


class CompletionDate(BaseModel):
    date: Union[date, None]
    plates: List[PlateSpecification] = Field(default_factory=list)

    @validator("date", pre=True)
    def parse_none(cls, v):
        if v == "None":
            return None
        return v


class Order(BaseModel):
    number: str
    production_days: int
    completion_dates: List[CompletionDate] = Field(default_factory=list)

class RetoolerSetting(BaseModel):
    height: int
    width: int


class ProductionSpecification(BaseModel):
    directory: Directory
    retooler: RetoolerSetting
    ready_plates: List[PlateSpecification] = Field(default_factory=list)
    available_tracks: List[AvailableTrack] = Field(default_factory=list)
    orders: List[Order] = Field(default_factory=list)
