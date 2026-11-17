from datetime import date
from sqlalchemy import String,Float,Date,ForeignKey,CheckConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base
class CalibrationCertificate(Base):
    __tablename__='calibration_certificates'
    __table_args__=(CheckConstraint("state in ('draft','issued')"),)
    id:Mapped[int]=mapped_column(primary_key=True)
    probe_id:Mapped[int]=mapped_column(ForeignKey('probes.id'))
    code:Mapped[str]=mapped_column(String(60),unique=True)
    zero_error:Mapped[float]=mapped_column(Float)
    span_error:Mapped[float]=mapped_column(Float)
    valid_until:Mapped[date]=mapped_column(Date)
    state:Mapped[str]=mapped_column(String(20),default='draft')
    issued_by:Mapped[str|None]=mapped_column(String(100),nullable=True)
    issued_at:Mapped[str|None]=mapped_column(String(40),nullable=True)
