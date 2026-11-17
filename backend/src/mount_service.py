from fastapi import HTTPException
from sqlalchemy import select
from .models import Layout
from .mount_models import ModelMount,RunMount
from .run_models import TunnelRun
from .calibration_service import locked
from .services import pack,audit
RHO_KG_M3=1.225
GRAVITY_M_S2=9.80665

def create(s,d,u):
    l=locked(s,Layout,d.layout_id)
    if l.status!='signed':raise HTTPException(409,'仅已审签布局可登记翼模装夹')
    x=ModelMount(**d.model_dump());s.add(x);s.flush();audit(s,u,'登记翼模装夹 '+x.code);return pack(x)
def revise(s,id,d,u):
    x=locked(s,ModelMount,id)
    if x.state!='draft':raise HTTPException(409,'已验收装夹不能修改，请新建装夹记录')
    if x.code!=d.code or x.layout_id!=d.layout_id:raise HTTPException(409,'装夹编号和布局不可修改')
    for k,v in d.model_dump().items():setattr(x,k,v)
    audit(s,u,'修订翼模装夹 '+x.code);return pack(x)
def accept(s,id,u):
    x=locked(s,ModelMount,id)
    if x.state!='draft':raise HTTPException(409,'装夹已验收，不能重复签署')
    if not 20<=x.torque_nm<=80:raise HTTPException(409,'固定扭矩须在20–80N·m内')
    x.state='accepted';x.accepted_by=u.email;audit(s,u,'主管验收装夹 '+x.code);return pack(x)
def link(s,d,u,replace=False):
    r=locked(s,TunnelRun,d.run_id);m=locked(s,ModelMount,d.mount_id)
    if r.state!='planned':raise HTTPException(409,'只能为未开车计划关联装夹')
    if m.state!='accepted' or m.layout_id!=r.layout_id:raise HTTPException(409,'须匹配本试验布局且已验收的装夹')
    x=s.scalar(select(RunMount).where(RunMount.run_id==r.id).with_for_update())
    if x and not replace:raise HTTPException(409,'试验已关联装夹，可在开车前修订关联')
    if not x:x=RunMount(**d.model_dump());s.add(x)
    else:x.mount_id=m.id
    s.flush();audit(s,u,'关联试验装夹 '+str(r.id)+'→'+m.code);return pack(x)
def readiness(s,r):
    link=s.scalar(select(RunMount).where(RunMount.run_id==r.id).with_for_update())
    if not link:raise HTTPException(409,'新开车须先关联已验收翼模装夹')
    m=locked(s,ModelMount,link.mount_id)
    if m.state!='accepted' or m.layout_id!=r.layout_id:raise HTTPException(409,'翼模装夹与本试验布局不匹配或未验收')
    q=.5*RHO_KG_M3*r.speed**2;wind=q*m.area_m2;weight=m.mass_kg*GRAVITY_M_S2;load=wind+weight
    if load>m.load_limit:raise HTTPException(409,'动压面积载荷加静重超过装夹核准载荷N')
    return {'mount':pack(m),'rho_kg_m3':RHO_KG_M3,'gravity_m_s2':GRAVITY_M_S2,'dynamic_pressure_pa':round(q,6),'wind_load_n':round(wind,6),'weight_n':round(weight,6),'estimated_load_n':round(load,6),'formula':'0.5 * rho_kg_m3 * speed_m_s^2 * area_m2 + mass_kg * gravity_m_s2'}
