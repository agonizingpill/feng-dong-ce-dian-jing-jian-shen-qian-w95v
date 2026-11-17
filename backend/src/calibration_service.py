from datetime import datetime,date,timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select
from fastapi import HTTPException
from .models import Probe
from .calibration_models import CalibrationCertificate
from .services import get,pack,audit
ZERO_LIMIT=.5
SPAN_LIMIT=1.0

def today():return datetime.now(ZoneInfo('Asia/Shanghai')).date()
def locked(s,cls,id):
    x=s.scalar(select(cls).where(cls.id==id).with_for_update().execution_options(populate_existing=True))
    if not x:raise HTTPException(404,'测点、证书或试验记录不存在')
    return x

def view(s,x):
    return {k:v.isoformat() if isinstance(v,date) else v for k,v in pack(x).items()}|{'probe_code':get(s,Probe,x.probe_id).code}
def create(s,d,u):
    get(s,Probe,d.probe_id);x=CalibrationCertificate(**d.model_dump());s.add(x);s.flush();audit(s,u,'登记校准证书 '+x.code);return view(s,x)
def revise(s,id,d,u):
    x=locked(s,CalibrationCertificate,id)
    if x.state!='draft':raise HTTPException(409,'已签发证书不可覆盖，请登记新证书')
    if x.probe_id!=d.probe_id or x.code!=d.code:raise HTTPException(409,'证书测点与编号不可变更')
    for k,v in d.model_dump().items():setattr(x,k,v)
    audit(s,u,'修订校准证书 '+x.code);return view(s,x)
def validate(x):
    if abs(x.zero_error)>ZERO_LIMIT or abs(x.span_error)>SPAN_LIMIT:raise HTTPException(409,'校准误差超限：零点须≤±0.5Pa，跨度须≤±1%')
    if x.valid_until<today():raise HTTPException(409,'校准证书已过有效期')
def issue(s,id,u):
    preview=get(s,CalibrationCertificate,id);locked(s,Probe,preview.probe_id);x=locked(s,CalibrationCertificate,id)
    if x.state!='draft':raise HTTPException(409,'证书已经签发，不得重复签署')
    validate(x);x.state='issued';x.issued_by=u.email;x.issued_at=datetime.now(timezone.utc).isoformat();audit(s,u,'负责人签发校准 '+x.code);return view(s,x)
def current_certificate(s,probe):
    x=s.scalar(select(CalibrationCertificate).where(CalibrationCertificate.probe_id==probe.id,CalibrationCertificate.state=='issued').order_by(CalibrationCertificate.issued_at.desc(),CalibrationCertificate.id.desc()).with_for_update())
    if not x:raise HTTPException(409,f'{probe.code}缺少负责人签发的校准证书')
    validate(x);return x
