from sqlalchemy import String,Integer,Float,Boolean,ForeignKey,JSON,CheckConstraint,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base
class User(Base):
    __tablename__='users'
    id:Mapped[int]=mapped_column(primary_key=True)
    email:Mapped[str]=mapped_column(String(100),unique=True)
    password_hash:Mapped[str]=mapped_column(String(180))
    role:Mapped[str]=mapped_column(String(20))
class Probe(Base):
    __tablename__='probes'
    __table_args__=(CheckConstraint('x_m >= 0 AND y_m >= 0'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(24),unique=True)
    zone:Mapped[str]=mapped_column(String(12))
    x_m:Mapped[float]=mapped_column(Float)
    y_m:Mapped[float]=mapped_column(Float)
    calibrated:Mapped[bool]=mapped_column(Boolean,default=False)
    enabled:Mapped[bool]=mapped_column(Boolean,default=True)
class Sweep(Base):
    __tablename__='sweeps'
    __table_args__=(CheckConstraint('speed > 0 AND speed <= 100 AND angle >= -30 AND angle <= 30'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(32),unique=True)
    speed:Mapped[float]=mapped_column(Float)
    angle:Mapped[float]=mapped_column(Float)
    lift:Mapped[float]=mapped_column(Float)
class Pressure(Base):
    __tablename__='pressures'
    id:Mapped[int]=mapped_column(primary_key=True)
    sweep_id:Mapped[int]=mapped_column(ForeignKey('sweeps.id'))
    probe_id:Mapped[int]=mapped_column(ForeignKey('probes.id'))
    pascal:Mapped[float]=mapped_column(Float)
    __table_args__=(UniqueConstraint('sweep_id','probe_id'),)
class Layout(Base):
    __tablename__='layouts'
    __table_args__=(CheckConstraint('max_channels > 0 AND max_channels <= 12'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(40),unique=True)
    max_channels:Mapped[int]=mapped_column(Integer)
    status:Mapped[str]=mapped_column(String(20),default='calculating')
    auto_select:Mapped[bool]=mapped_column(Boolean,default=True)
    evidence:Mapped[dict|None]=mapped_column(JSON,nullable=True)
    source_checksum:Mapped[str|None]=mapped_column(String(64),nullable=True)
    signed_by:Mapped[str|None]=mapped_column(String(100),nullable=True)
class LayoutProbe(Base):
    __tablename__='layout_probes'
    id:Mapped[int]=mapped_column(primary_key=True)
    layout_id:Mapped[int]=mapped_column(ForeignKey('layouts.id'))
    probe_id:Mapped[int]=mapped_column(ForeignKey('probes.id'))
    __table_args__=(UniqueConstraint('layout_id','probe_id'),)
class Audit(Base):
    __tablename__='audits'
    id:Mapped[int]=mapped_column(primary_key=True)
    actor:Mapped[str]=mapped_column(String(100))
    action:Mapped[str]=mapped_column(String(200))
    stamp:Mapped[str]=mapped_column(String(40))
