from datetime import datetime,timezone
from fastapi import HTTPException
from sqlalchemy import select
from .models import Probe
from .calibration_models import CalibrationCertificate
from .run_models import TunnelRun
from .revocation_models import CertificateRevocation,AffectedRun
from .calibration_service import locked
from .services import get,pack,audit

def revocation_of(s,certificate_id):
    return s.scalar(select(CertificateRevocation).where(CertificateRevocation.certificate_id==certificate_id))
def run_affected(s,run_id):
    return s.scalar(select(AffectedRun.id).where(AffectedRun.run_id==run_id).limit(1)) is not None
def assert_not_affected(s,run_id,action):
    if run_affected(s,run_id):raise HTTPException(409,f'本试验开车所用校准证书已被撤销，停止{action}')
def view(s,rev):
    cert=get(s,CalibrationCertificate,rev.certificate_id)
    runs=s.scalars(select(TunnelRun).join(AffectedRun,AffectedRun.run_id==TunnelRun.id).where(AffectedRun.revocation_id==rev.id).order_by(TunnelRun.id)).all()
    return pack(rev)|{'certificate_code':cert.code,'probe_code':get(s,Probe,cert.probe_id).code,'affected_runs':[{'id':r.id,'code':r.code,'state':r.state} for r in runs]}
def runs_using(s,certificate_id):
    rows=s.scalars(select(TunnelRun).where(TunnelRun.snapshot.isnot(None))).all()
    return [r for r in rows if any(c.get('id')==certificate_id for c in (r.snapshot or {}).get('certificates',[]))]
def revoke(s,cert_id,d,u):
    x=locked(s,CalibrationCertificate,cert_id)
    existing=revocation_of(s,cert_id)
    if existing:return view(s,existing)
    if x.state!='issued':raise HTTPException(409,'仅已签发证书可撤销，草稿证书无需撤销')
    rev=CertificateRevocation(certificate_id=x.id,reason=d.reason,revoked_by=u.email,revoked_at=datetime.now(timezone.utc).isoformat())
    s.add(rev);s.flush()
    for r in sorted(runs_using(s,x.id),key=lambda r:r.id):
        locked(s,TunnelRun,r.id)
        s.add(AffectedRun(revocation_id=rev.id,run_id=r.id))
    s.flush();audit(s,u,'撤销误签校准证书 '+x.code);return view(s,rev)
