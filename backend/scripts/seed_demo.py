import random,math
from sqlalchemy import select,func
from src.db import Base,engine,Session
from src.models import User,Probe,Sweep,Pressure,Layout
from src.calibration_models import CalibrationCertificate
from src.run_models import TunnelRun
from datetime import datetime,timedelta,timezone
from src.mount_models import ModelMount,RunMount
from src.acquisition_models import AcquisitionBatch,ChannelReading
from src.delivery_models import TunnelDelivery
from src.auth import hash_password

def seed():
    Base.metadata.create_all(engine)
    with Session() as s:
        for role in ('admin','engineer','viewer'):
            email=role+'@yiheng.demo'
            if not s.scalar(select(User).where(User.email==email)):s.add(User(email=email,role=role,password_hash=hash_password('Tunnel2026!')))
        for i in range(12):
            code=f'P{i+1:02}'
            if not s.scalar(select(Probe).where(Probe.code==code)):s.add(Probe(code=code,zone=['root','mid','tip'][i//4],x_m=round(.12+(i%4)*.18,2),y_m=round(.2+(i//4)*.8,2),calibrated=i!=11,enabled=True))
        s.flush();probes=s.scalars(select(Probe).order_by(Probe.id)).all();rng=random.Random(42)
        for i in range(120):
            code=f'SW-{i+1:03}';speed=round(rng.uniform(18,42),2);angle=round(rng.uniform(-4,16),2)
            # Each region has a partially independent pressure contribution to total lift.
            latent=[rng.gauss(0,1)for _ in range(3)]
            pressure=[round(100+angle*2+speed*.5+latent[j//4]*(8-(j%4))+rng.gauss(0,1.2+(j%4)),3)for j in range(12)]
            lift=round(30+.18*pressure[0]+.14*pressure[4]+.11*pressure[8]+rng.gauss(0,.25),3)
            sweep=s.scalar(select(Sweep).where(Sweep.code==code))
            if not sweep:sweep=Sweep(code=code,speed=speed,angle=angle,lift=lift);s.add(sweep);s.flush()
            for p,value in zip(probes,pressure):
                if not s.scalar(select(Pressure).where(Pressure.sweep_id==sweep.id,Pressure.probe_id==p.id)):s.add(Pressure(sweep_id=sweep.id,probe_id=p.id,pascal=value))
        for probe_code in ('P01','P05','P09'):
            cert_code='CAL-SEED-'+probe_code
            if not s.scalar(select(CalibrationCertificate).where(CalibrationCertificate.code==cert_code)):
                probe=s.scalar(select(Probe).where(Probe.code==probe_code))
                now=datetime.now(timezone.utc)
                expiry=now.date()+timedelta(days=-1 if probe_code=='P09' else 365)
                s.add(CalibrationCertificate(probe_id=probe.id,code=cert_code,zero_error=.05,span_error=.2,valid_until=expiry,state='issued',issued_by='seed:lab-archive',issued_at=(now-timedelta(days=30)).isoformat()))
        s.commit();print({t.__tablename__:s.scalar(select(func.count()).select_from(t))for t in (User,Probe,Sweep,Pressure,Layout,CalibrationCertificate,TunnelRun,ModelMount,RunMount,AcquisitionBatch,ChannelReading,TunnelDelivery)})
if __name__=='__main__':seed()
