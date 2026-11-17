from datetime import date
from pydantic import BaseModel,Field,ConfigDict,field_validator
class CertificateInput(BaseModel):
    probe_id:int
    code:str=Field(min_length=4,max_length=60)
    zero_error:float=Field(ge=-20,le=20,allow_inf_nan=False)
    span_error:float=Field(ge=-20,le=20,allow_inf_nan=False)
    valid_until:date
    @field_validator('code')
    @classmethod
    def code_not_empty(cls,v):
        if not v.strip():raise ValueError('证书编号不能为空')
        return v.strip()
class Interlocks(BaseModel):
    model_config=ConfigDict(extra='forbid')
    air_path_clear:bool=False
    emergency_stop_tested:bool=False
    model_secured:bool=False
class RunInput(BaseModel):
    layout_id:int
    code:str=Field(min_length=4,max_length=60)
    speed:float=Field(gt=0,le=100,allow_inf_nan=False)
    target_angle:float=Field(ge=-30,le=30,allow_inf_nan=False)
    checklist:Interlocks=Field(default_factory=Interlocks)
class FinishInput(BaseModel):
    result_note:str=Field(min_length=8,max_length=2000)
    @field_validator('result_note')
    @classmethod
    def not_blank(cls,v):
        if len(v.strip())<8:raise ValueError('至少8字试验收尾说明')
        return v.strip()
