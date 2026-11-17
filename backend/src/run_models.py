from sqlalchemy import String,Float,Text,JSON,ForeignKey,CheckConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base
class TunnelRun(Base):
    __tablename__='tunnel_runs'
    __table_args__=(CheckConstraint("state in ('planned','running','completed')"),CheckConstraint('speed > 0 AND speed <= 100 AND target_angle >= -30 AND target_angle <= 30'))
    id:Mapped[int]=mapped_column(primary_key=True)
    layout_id:Mapped[int]=mapped_column(ForeignKey('layouts.id'))
    code:Mapped[str]=mapped_column(String(60),unique=True)
    speed:Mapped[float]=mapped_column(Float)
    target_angle:Mapped[float]=mapped_column(Float)
    checklist:Mapped[dict]=mapped_column(JSON)
    state:Mapped[str]=mapped_column(String(20),default='planned')
    snapshot:Mapped[dict|None]=mapped_column(JSON,nullable=True)
    started_by:Mapped[str|None]=mapped_column(String(100),nullable=True)
    started_at:Mapped[str|None]=mapped_column(String(40),nullable=True)
    completed_at:Mapped[str|None]=mapped_column(String(40),nullable=True)
    result_note:Mapped[str]=mapped_column(Text,default='')
