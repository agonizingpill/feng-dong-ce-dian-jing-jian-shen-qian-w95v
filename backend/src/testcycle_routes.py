from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from .db import db_session
from .auth import current,writers,admin
from .mount_models import ModelMount,RunMount
from .acquisition_models import AcquisitionBatch
from .delivery_models import TunnelDelivery
from .testcycle_schemas import MountInput,MountLinkInput,BatchInput,ReadingsInput,DeliveryInput,ReceiptInput
from .services import pack
from . import mount_service as mounts,acquisition_service as acq,delivery_service as deliveries,revocation_service as revocation
router=APIRouter()
@router.get('/model-mounts')
def list_mounts(s=Depends(db_session),u=Depends(current)):return [pack(x) for x in s.scalars(select(ModelMount).order_by(ModelMount.id.desc()))]
@router.post('/model-mounts')
def create_mount(d:MountInput,s=Depends(db_session),u=Depends(writers)):
    x=mounts.create(s,d,u);s.commit();return x
@router.put('/model-mounts/{id}')
def revise_mount(id:int,d:MountInput,s=Depends(db_session),u=Depends(writers)):
    x=mounts.revise(s,id,d,u);s.commit();return x
@router.post('/model-mounts/{id}/accept')
def accept(id:int,s=Depends(db_session),u=Depends(admin)):
    x=mounts.accept(s,id,u);s.commit();return x
@router.get('/run-mounts')
def links(s=Depends(db_session),u=Depends(current)):return [pack(x) for x in s.scalars(select(RunMount).order_by(RunMount.id))]
@router.post('/run-mounts')
def link(d:MountLinkInput,s=Depends(db_session),u=Depends(writers)):
    x=mounts.link(s,d,u);s.commit();return x
@router.put('/run-mounts/{run_id}')
def relink(run_id:int,d:MountLinkInput,s=Depends(db_session),u=Depends(writers)):
    if run_id!=d.run_id:raise HTTPException(409,'试验关联不能跨单修订')
    x=mounts.link(s,d,u,True);s.commit();return x
@router.get('/acquisition-batches')
def batches(s=Depends(db_session),u=Depends(current)):return [acq.view(s,x) for x in s.scalars(select(AcquisitionBatch).order_by(AcquisitionBatch.id.desc()))]
@router.post('/acquisition-batches')
def create_batch(d:BatchInput,s=Depends(db_session),u=Depends(writers)):
    x=acq.create(s,d,u);s.commit();return x
@router.put('/acquisition-batches/{id}/readings')
def readings(id:int,d:ReadingsInput,s=Depends(db_session),u=Depends(writers)):
    x=acq.write(s,id,d,u);s.commit();return x
@router.post('/acquisition-batches/{id}/freeze')
def freeze(id:int,s=Depends(db_session),u=Depends(admin)):
    x=acq.freeze(s,id,u);s.commit();return x
@router.get('/tunnel-deliveries')
def list_deliveries(s=Depends(db_session),u=Depends(current)):return [pack(x)|{'affected':revocation.run_affected(s,x.run_id)} for x in s.scalars(select(TunnelDelivery).order_by(TunnelDelivery.id.desc()))]
@router.post('/tunnel-deliveries')
def delivery(d:DeliveryInput,s=Depends(db_session),u=Depends(writers)):
    x=deliveries.create(s,d,u);s.commit();return x
@router.post('/tunnel-deliveries/{id}/approve')
def approve(id:int,s=Depends(db_session),u=Depends(admin)):
    x=deliveries.approve(s,id,u);s.commit();return x
@router.post('/tunnel-deliveries/{id}/acknowledge')
def acknowledge(id:int,d:ReceiptInput,s=Depends(db_session),u=Depends(writers)):
    x=deliveries.acknowledge(s,id,d,u);s.commit();return x
