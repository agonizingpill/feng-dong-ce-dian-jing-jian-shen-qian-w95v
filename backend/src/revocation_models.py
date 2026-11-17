from sqlalchemy import String,Text,ForeignKey,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base
class CertificateRevocation(Base):
    __tablename__='certificate_revocations'
    __table_args__=(UniqueConstraint('certificate_id'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    certificate_id:Mapped[int]=mapped_column(ForeignKey('calibration_certificates.id'))
    reason:Mapped[str]=mapped_column(Text)
    revoked_by:Mapped[str]=mapped_column(String(100))
    revoked_at:Mapped[str]=mapped_column(String(40))
class AffectedRun(Base):
    __tablename__='affected_runs'
    __table_args__=(UniqueConstraint('revocation_id','run_id'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    revocation_id:Mapped[int]=mapped_column(ForeignKey('certificate_revocations.id'))
    run_id:Mapped[int]=mapped_column(ForeignKey('tunnel_runs.id'))
