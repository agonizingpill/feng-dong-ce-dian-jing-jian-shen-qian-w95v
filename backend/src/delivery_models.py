from sqlalchemy import String,Text,ForeignKey,JSON,CheckConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base
class TunnelDelivery(Base):
    __tablename__='tunnel_deliveries'
    __table_args__=(CheckConstraint("state in ('submitted','approved','acknowledged')"),)
    id:Mapped[int]=mapped_column(primary_key=True)
    run_id:Mapped[int]=mapped_column(ForeignKey('tunnel_runs.id'),unique=True)
    recipient:Mapped[str]=mapped_column(String(100))
    state:Mapped[str]=mapped_column(String(20),default='submitted')
    snapshot:Mapped[dict]=mapped_column(JSON)
    approved_by:Mapped[str|None]=mapped_column(String(100),nullable=True)
    receipt:Mapped[str]=mapped_column(Text,default='')
