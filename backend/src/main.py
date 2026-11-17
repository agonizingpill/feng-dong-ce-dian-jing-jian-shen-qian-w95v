import os,logging
from contextlib import asynccontextmanager
import redis
from sqlalchemy import select,delete
from sqlalchemy.exc import IntegrityError
from fastapi import FastAPI,Depends,HTTPException
from fastapi.responses import JSONResponse
from .db import Base,engine,db_session
from .models import User,Probe,Sweep,Pressure,Layout,LayoutProbe,Audit
from .auth import current,writers,admin,verify,token
from .schemas import Login,ProbeInput,SweepInput,LayoutInput,Selection
from .services import get,pack,pack_layout,pack_sweep,audit,invalidate,assign,check_sign
from .middlewares import RequestTrace,BurstGuard
from .readiness_routes import router as readiness_router
from .testcycle_routes import router as testcycle_router
from .constants import ROLES,ZONES,LAYOUT_STATES
r=redis.Redis.from_url(os.environ['REDIS_URL'],decode_responses=True)
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    if os.getenv('SEED_DEMO','true')=='true':
        try:
            from scripts.seed_demo import seed
            seed()
        except Exception:logging.exception('seed failed')
    yield
app=FastAPI(title='翼衡 · 风洞测点精简审签',lifespan=lifespan);app.include_router(readiness_router);app.include_router(testcycle_router);app.add_middleware(RequestTrace);app.add_middleware(BurstGuard)
@app.exception_handler(IntegrityError)
async def conflict(req,exc):return JSONResponse({'detail':'编号重复、测点重复或关联条件不满足，请核对'},409)
@app.get('/health')
def health(s=Depends(db_session)):s.execute(select(1));r.ping();return {'status':'ok'}
@app.post('/auth/login')
def login(p:Login,s=Depends(db_session)):
    u=s.scalar(select(User).where(User.email==p.email))
    if not u or not verify(p.password,u.password_hash):raise HTTPException(401,'邮箱或口令不正确')
    return {'token':token(u),'user':{'email':u.email,'role':u.role}}
@app.get('/me')
def me(u=Depends(current)):return {'email':u.email,'role':u.role}
@app.get('/enums')
def enums(u=Depends(current)):return {'roles':ROLES,'zones':ZONES,'layout_states':LAYOUT_STATES}
@app.get('/probes')
def probes(s=Depends(db_session),u=Depends(current)):return [pack(x)for x in s.scalars(select(Probe).order_by(Probe.id))]
@app.put('/probes/{pid}')
def probe(pid:int,p:ProbeInput,s=Depends(db_session),u=Depends(writers)):
    v=get(s,Probe,pid);invalidate(s)
    for k,value in p.model_dump().items():setattr(v,k,value)
    audit(s,u,'修订标定 '+v.code);s.commit();return pack(v)
@app.get('/sweeps')
def sweeps(s=Depends(db_session),u=Depends(current)):return [pack_sweep(s,x)for x in s.scalars(select(Sweep).order_by(Sweep.id))]
def write_sweep(s,p,v=None):
    probes=s.scalars(select(Probe).order_by(Probe.id)).all()
    if set(p.pressures)!={x.code for x in probes}:raise HTTPException(409,'压力记录须覆盖全部已登记测点代码')
    if any(not -10000<=x<=10000 for x in p.pressures.values()):raise HTTPException(409,'压力超出传感器量程±10000Pa')
    invalidate(s)
    if not v:v=Sweep(code=p.code,speed=p.speed,angle=p.angle,lift=p.lift);s.add(v);s.flush()
    else:
        for k in ('code','speed','angle','lift'):setattr(v,k,getattr(p,k))
        s.execute(delete(Pressure).where(Pressure.sweep_id==v.id))
    for probe in probes:s.add(Pressure(sweep_id=v.id,probe_id=probe.id,pascal=p.pressures[probe.code]))
    return v
@app.post('/sweeps')
def add_sweep(p:SweepInput,s=Depends(db_session),u=Depends(writers)):
    v=write_sweep(s,p);audit(s,u,'录入扫角 '+v.code);s.commit();return pack_sweep(s,v)
@app.put('/sweeps/{sid}')
def edit_sweep(sid:int,p:SweepInput,s=Depends(db_session),u=Depends(writers)):
    v=write_sweep(s,p,get(s,Sweep,sid));audit(s,u,'修订扫角 '+v.code);s.commit();return pack_sweep(s,v)
@app.get('/layouts')
def layouts(s=Depends(db_session),u=Depends(current)):return [pack_layout(s,x)for x in s.scalars(select(Layout).order_by(Layout.id.desc()))]
def enqueue(s,l):
    l.status='calculating';l.evidence=None;l.source_checksum=None;s.commit()
    try:r.rpush('tunnel-selection',l.id)
    except Exception:l.status='failed';s.commit();raise HTTPException(503,'计算队列暂不可用，请重试')
@app.post('/layouts')
def add_layout(p:LayoutInput,s=Depends(db_session),u=Depends(writers)):
    l=Layout(**p.model_dump(),auto_select=True,status='calculating');s.add(l);audit(s,u,'建立通道方案 '+p.code);enqueue(s,l);return pack_layout(s,l)
@app.put('/layouts/{lid}/probes')
def reselect(lid:int,p:Selection,s=Depends(db_session),u=Depends(writers)):
    l=get(s,Layout,lid)
    if l.status in ('signed','calculating'):raise HTTPException(409,'已审签或计算中的方案不能改点')
    assign(s,l,p.probe_ids);l.auto_select=False;audit(s,u,'人工修订测点 '+l.code);enqueue(s,l);return pack_layout(s,l)
@app.post('/layouts/{lid}/sign')
def sign(lid:int,s=Depends(db_session),u=Depends(admin)):
    l=s.query(Layout).filter_by(id=lid).with_for_update().one_or_none()
    if not l:raise HTTPException(404,'布置方案不存在')
    check_sign(s,l);l.status='signed';l.signed_by=u.email;audit(s,u,'审签布置 '+l.code);s.commit();return pack_layout(s,l)
@app.get('/audits')
def audits(s=Depends(db_session),u=Depends(current)):return [pack(x)for x in s.scalars(select(Audit).order_by(Audit.id.desc()).limit(30))]
