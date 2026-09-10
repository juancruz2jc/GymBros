import uuid
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey, UniqueConstraint
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID 
# pyrefly: ignore [missing-import]
from sqlalchemy.sql import func
from app.models.base import Base


class Racha(Base):
    __tablename__ = "rachas"

    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    racha_actual = Column(Integer, default=0, nullable=False)
    racha_maxima = Column(Integer, default=0, nullable=False)
    ultima_actividad = Column(Date, nullable=True)


class LogroUsuario(Base):
    __tablename__ = "logros_usuario"
    __table_args__ = (
        UniqueConstraint('usuario_id', 'tipo_logro', name='uq_usuario_tipo_logro'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), index=True, nullable=False)
    tipo_logro = Column(String(50), nullable=False)
    obtenido_en = Column(DateTime(timezone=True), server_default=func.now())