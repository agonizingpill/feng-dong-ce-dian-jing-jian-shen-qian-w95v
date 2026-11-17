from datetime import datetime,timezone
import hashlib,json
from fastapi import HTTPException
from sqlalchemy import select,delete
from .models import Probe,Sweep,Pressure,Layout,LayoutProbe,Audit

def get(s,cls,id):
    v=s.get(cls,id)
    if not v:raise HTTPException(404,'记录不存在')
    return v
def pack(v):return {c.name:getattr(v,c.name) for c in v.__table__.columns}
def selected(s,lid):return list(s.scalars(select(LayoutProbe.probe_id).where(LayoutProbe.layout_id==lid).order_by(LayoutProbe.probe_id)))
def pack_layout(s,l):return pack(l)|{'probe_ids':selected(s,l.id)}
def pack_sweep(s,x):
    return pack(x)|{'pressures':{probe.code:pressure.pascal for pressure,probe in s.execute(select(Pressure,Probe).join(Probe,Probe.id==Pressure.probe_id).where(Pressure.sweep_id==x.id))}}
def audit(s,u,action):s.add(Audit(actor=u.email,action=action,stamp=datetime.now(timezone.utc).isoformat()))
def invalidate(s):
    if s.scalar(select(Layout.id).where(Layout.status=='signed')):raise HTTPException(409,'已有审签布置，标定与扫角来源已冻结')
    if s.scalar(select(Layout.id).where(Layout.status=='calculating')):raise HTTPException(409,'贡献计算进行中，来源暂不能修改')
    for l in s.scalars(select(Layout).where(Layout.status.in_(['ready','failed']))):l.status='invalidated';l.evidence=None;l.source_checksum=None

def assign(s,l,ids):
    if len(ids)!=len(set(ids)):raise HTTPException(409,'测点不能重复占用通道')
    if len(ids)>l.max_channels:raise HTTPException(409,'所选测点超过本方案通道预算')
    probes=[get(s,Probe,i) for i in ids]
    if any(not p.enabled for p in probes):raise HTTPException(409,'停用测点不能加入布置')
    s.execute(delete(LayoutProbe).where(LayoutProbe.layout_id==l.id))
    for id in ids:s.add(LayoutProbe(layout_id=l.id,probe_id=id))

def source_checksum(s):
    content={'probes':[pack(p) for p in s.scalars(select(Probe).order_by(Probe.id))],'sweeps':[pack_sweep(s,x)for x in s.scalars(select(Sweep).order_by(Sweep.id))]}
    return hashlib.sha256(json.dumps(content,sort_keys=True).encode()).hexdigest()

def check_sign(s,l):
    if l.status!='ready':raise HTTPException(409,'仅最新计算完成的方案可审签')
    ids=selected(s,l.id);probes=[get(s,Probe,i) for i in ids]
    if not probes or len(probes)>l.max_channels:raise HTTPException(409,'测点数超过通道预算或尚未选点')
    if any(not p.calibrated or not p.enabled for p in probes):raise HTTPException(409,'包含未标定或已停用测点，不能审签')
    if set(p.zone for p in probes)!={'root','mid','tip'}:raise HTTPException(409,'布置须同时覆盖翼根、翼中、翼尖')
    if l.source_checksum!=source_checksum(s):raise HTTPException(409,'来源校验已变化，请重新计算')
