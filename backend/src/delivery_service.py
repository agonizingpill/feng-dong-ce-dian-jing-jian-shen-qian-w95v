from copy import deepcopy
from fastapi import HTTPException
from sqlalchemy import select
from .run_models import TunnelRun
from .acquisition_models import AcquisitionBatch
from .acquisition_service import view as batch_view
from .delivery_models import TunnelDelivery
from .calibration_service import locked
from .services import pack,audit

def create(s,d,u):
    r=locked(s,TunnelRun,d.run_id)
    if r.state!='completed':raise HTTPException(409,'仅已完结试验可以提交交付复核')
    b=s.scalar(select(AcquisitionBatch).where(AcquisitionBatch.run_id==r.id).with_for_update())
    if not b or b.state!='frozen' or not b.summary or b.summary['missing_rate']!=0:raise HTTPException(409,'须完整覆盖通道并由主管冻结采集后交付')
    if not r.snapshot or 'mounting' not in r.snapshot:raise HTTPException(409,'缺少可追溯装夹快照，旧试验不可伪补发布')
    if s.scalar(select(TunnelDelivery.id).where(TunnelDelivery.run_id==r.id)):raise HTTPException(409,'本试验已有交付单，不得重复发布')
    x=TunnelDelivery(**d.model_dump(),snapshot=deepcopy({'run':pack(r),'acquisition':batch_view(s,b)}));s.add(x);s.flush();audit(s,u,'提交试验交付 '+str(x.id));return pack(x)
def approve(s,id,u):
    x=locked(s,TunnelDelivery,id)
    if x.state!='submitted':raise HTTPException(409,'仅待复核交付可核准，不能重复发布')
    x.state='approved';x.approved_by=u.email;audit(s,u,'主管核准交付 '+str(id));return pack(x)
def acknowledge(s,id,d,u):
    x=locked(s,TunnelDelivery,id)
    if x.state!='approved':raise HTTPException(409,'交付须主管核准，已回执不能重复')
    if len(d.receipt.strip())<8:raise HTTPException(409,'回执说明至少8字')
    x.receipt=d.receipt.strip();x.state='acknowledged';audit(s,u,'登记试验交付回执 '+str(id));return pack(x)
