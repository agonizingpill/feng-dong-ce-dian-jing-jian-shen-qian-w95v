from pydantic import BaseModel,Field,model_validator
from typing import Annotated
class MountInput(BaseModel):
    code:str=Field(min_length=3,max_length=60,pattern=r'\S')
    layout_id:int
    mass_kg:float=Field(gt=0,le=1000,allow_inf_nan=False)
    area_m2:float=Field(ge=.01,le=10,allow_inf_nan=False)
    torque_nm:float=Field(ge=0,le=200,allow_inf_nan=False)
    load_limit:float=Field(gt=0,le=100000,allow_inf_nan=False)
class MountLinkInput(BaseModel):
    run_id:int
    mount_id:int
class BatchInput(BaseModel):
    run_id:int
    sample_rate:int=Field(ge=1,le=1000)
    expected_seconds:int=Field(ge=1,le=60)
    @model_validator(mode='after')
    def bounded(self):
        if self.sample_rate*self.expected_seconds>20000:raise ValueError('小型批次每通道最多20000个预期样本')
        return self
class ReadingInput(BaseModel):
    probe_id:int
    values:list[Annotated[float,Field(ge=-10000,le=10000,allow_inf_nan=False)]]=Field(min_length=1,max_length=20000)
class ReadingsInput(BaseModel):
    readings:list[ReadingInput]=Field(min_length=1,max_length=12)
class DeliveryInput(BaseModel):
    run_id:int
    recipient:str=Field(min_length=2,max_length=100,pattern=r'\S')
class ReceiptInput(BaseModel):
    receipt:str=Field(min_length=8,max_length=2000,pattern=r'\S')
