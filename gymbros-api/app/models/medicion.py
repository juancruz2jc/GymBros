import uuid
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Date, DateTime, Numeric, ForeignKey
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID
# pyrefly: ignore [missing-import]
from sqlalchemy.sql import func
from app.models.base import Base


class Medicion(Base):
    __tablename__ = "mediciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), index=True, nullable=False)
    fecha = Column(Date, nullable=False)
    peso_kg = Column(Numeric(5, 2), nullable=False)
    porcentaje_grasa = Column(Numeric(4, 2), nullable=True)
    masa_muscular_kg = Column(Numeric(5, 2), nullable=True)
    circunf_cintura_cm = Column(Numeric(5, 2), nullable=True)
    circunf_cadera_cm = Column(Numeric(5, 2), nullable=True)
    circunf_brazo_cm = Column(Numeric(5, 2), nullable=True)
    circunf_pierna_cm = Column(Numeric(5, 2), nullable=True)
    circunf_pecho_cm = Column(Numeric(5, 2), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())