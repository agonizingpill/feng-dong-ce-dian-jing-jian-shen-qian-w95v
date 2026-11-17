from sqlalchemy import String,Integer,Float,ForeignKey,JSON,UniqueConstraint,CheckConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base
class AcquisitionBatch(Base):
    __tablename__='acquisition_batches'
    __table_args__=(CheckConstraint('sample_rate > 0 AND expected_seconds > 0'),CheckConstraint("state in ('collecting','frozen')"))
    id:Mapped[int]=mapped_column(primary_key=True)
    run_id:Mapped[int]=mapped_column(ForeignKey('tunnel_runs.id'),unique=True)
    sample_rate:Mapped[int]=mapped_column(Integer)
    expected_seconds:Mapped[int]=mapped_column(Integer)
    state:Mapped[str]=mapped_column(String(20),default='collecting')
    summary:Mapped[dict|None]=mapped_column(JSON,nullable=True)
    frozen_by:Mapped[str|None]=mapped_column(String(100),nullable=True)
class ChannelReading(Base):
    __tablename__='channel_readings'
    __table_args__=(UniqueConstraint('batch_id','probe_id'),CheckConstraint('samples > 0'))
    id:Mapped[int]=mapped_column(primary_key=True)
    batch_id:Mapped[int]=mapped_column(ForeignKey('acquisition_batches.id'))
    probe_id:Mapped[int]=mapped_column(ForeignKey('probes.id'))
    values:Mapped[list]=mapped_column(JSON)
    value:Mapped[float]=mapped_column(Float)
    samples:Mapped[int]=mapped_column(Integer)
