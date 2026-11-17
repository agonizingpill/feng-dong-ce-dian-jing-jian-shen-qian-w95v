from fastapi import APIRouter,Depends
from sqlalchemy import select
from .db import db_session
from .auth import current,writers,admin
from .calibration_models import CalibrationCertificate
from .run_models import TunnelRun
from .readiness_schemas import CertificateInput,RunInput,FinishInput
from .services import pack
from . import calibration_service as calibration,runs_service as runs
router=APIRouter()
@router.get('/calibration-certificates')
def certificates(s=Depends(db_session),u=Depends(current)):return [calibration.view(s,x) for x in s.scalars(select(CalibrationCertificate).order_by(CalibrationCertificate.id.desc()))]
@router.post('/calibration-certificates')
def create_certificate(d:CertificateInput,s=Depends(db_session),u=Depends(writers)):
    x=calibration.create(s,d,u);s.commit();return x
@router.put('/calibration-certificates/{id}')
def revise_certificate(id:int,d:CertificateInput,s=Depends(db_session),u=Depends(writers)):
    x=calibration.revise(s,id,d,u);s.commit();return x
@router.post('/calibration-certificates/{id}/issue')
def issue(id:int,s=Depends(db_session),u=Depends(admin)):
    x=calibration.issue(s,id,u);s.commit();return x
@router.get('/tunnel-runs')
def list_runs(s=Depends(db_session),u=Depends(current)):return [pack(x) for x in s.scalars(select(TunnelRun).order_by(TunnelRun.id.desc()))]
@router.post('/tunnel-runs')
def create_run(d:RunInput,s=Depends(db_session),u=Depends(writers)):
    x=runs.create(s,d,u);s.commit();return x
@router.put('/tunnel-runs/{id}')
def revise_run(id:int,d:RunInput,s=Depends(db_session),u=Depends(writers)):
    x=runs.revise(s,id,d,u);s.commit();return x
@router.post('/tunnel-runs/{id}/start')
def start(id:int,s=Depends(db_session),u=Depends(admin)):
    x=runs.start(s,id,u);s.commit();return x
@router.post('/tunnel-runs/{id}/complete')
def complete(id:int,d:FinishInput,s=Depends(db_session),u=Depends(writers)):
    x=runs.finish(s,id,d,u);s.commit();return x
