import numpy as np
from sqlalchemy import select
from sklearn.feature_selection import mutual_info_regression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from .models import Probe,Sweep,Pressure
from .services import selected,assign,source_checksum

def calculate(s,l):
    probes=s.scalars(select(Probe).where(Probe.enabled==True).order_by(Probe.id)).all()
    rows=s.scalars(select(Sweep).order_by(Sweep.id)).all()
    if len(rows)<40:raise ValueError('至少40组完整扫角才可精简测点')
    values={(p.sweep_id,p.probe_id):p.pascal for p in s.scalars(select(Pressure))}
    try:x=np.array([[values[(r.id,p.id)] for p in probes]for r in rows]);y=np.array([r.lift for r in rows])
    except KeyError:raise ValueError('扫角存在缺测点，不能计算贡献')
    ix=np.arange(len(rows));train,test=train_test_split(ix,test_size=.2,random_state=42)
    # Selection and standardization see training rows only. Holdout is evaluation only.
    mi=mutual_info_regression(x[train],y[train],random_state=42)
    order=np.argsort(-mi,kind='stable')
    if l.auto_select:assign(s,l,[probes[i].id for i in order[:l.max_channels]])
    s.flush();ids=selected(s,l.id)
    col=[i for i,p in enumerate(probes)if p.id in ids]
    if not col:raise ValueError('没有选中的有效测点')
    model=make_pipeline(StandardScaler(),Ridge(alpha=1.0));model.fit(x[train][:,col],y[train])
    prediction=model.predict(x[test][:,col]);mae=mean_absolute_error(y[test],prediction)
    baseline=make_pipeline(StandardScaler(),Ridge(alpha=1.0));baseline.fit(x[train],y[train]);full_mae=mean_absolute_error(y[test],baseline.predict(x[test]))
    l.source_checksum=source_checksum(s)
    l.evidence={'train_rows':len(train),'holdout_rows':len(test),'seed':42,'selected_mae_n':round(float(mae),3),'full_mae_n':round(float(full_mae),3),'selected_probe_ids':ids,'ranking':[{'probe_id':probes[i].id,'code':probes[i].code,'zone':probes[i].zone,'calibrated':probes[i].calibrated,'mutual_information':round(float(mi[i]),5)}for i in order],'holdout':[{'sweep':rows[i].code,'actual':round(float(y[i]),3),'predicted':round(float(v),3)}for i,v in zip(test,prediction)],'train_sweep_codes':[rows[i].code for i in train],'holdout_sweep_codes':[rows[i].code for i in test],'selected_probe_snapshot':[{'id':p.id,'code':p.code,'zone':p.zone,'x_m':p.x_m,'y_m':p.y_m,'calibrated':p.calibrated} for p in probes if p.id in ids]}
