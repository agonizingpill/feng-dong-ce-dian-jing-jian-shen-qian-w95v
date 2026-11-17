from pydantic import BaseModel,Field
from typing import Literal
class Login(BaseModel):
    email:str
    password:str
class ProbeInput(BaseModel):
    zone:Literal['root','mid','tip']
    x_m:float=Field(ge=0,le=10)
    y_m:float=Field(ge=0,le=10)
    calibrated:bool
    enabled:bool
class SweepInput(BaseModel):
    code:str=Field(min_length=1,max_length=32)
    speed:float=Field(gt=0,le=100)
    angle:float=Field(ge=-30,le=30)
    lift:float=Field(ge=-10000,le=10000)
    pressures:dict[str,float]
class LayoutInput(BaseModel):
    code:str=Field(min_length=1,max_length=40)
    max_channels:int=Field(ge=1,le=12)
class Selection(BaseModel):
    probe_ids:list[int]=Field(min_length=1,max_length=12)
