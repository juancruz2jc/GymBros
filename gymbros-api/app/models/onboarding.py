import uuid
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID
# pyrefly: ignore [missing-import]
from sqlalchemy.sql import func
from app.models.base import Base


class RespuestasOnboarding(Base):
    __tablename__ = "respuestas_onboarding"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    tiempo_practicando = Column(String(50), nullable=False)
    objetivo = Column(String(50), nullable=False)
    dias_entrenamiento_semana = Column(Integer, nullable=False)
    limitaciones_fisicas = Column(Text, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class CatalogoExperiencias(Base):
    __tablename__ = "catalogo_experiencias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)


class RespuestaExperiencias(Base):
    __tablename__ = "respuesta_experiencias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    respuesta_onboarding_id = Column(UUID(as_uuid=True), ForeignKey("respuestas_onboarding.id", ondelete="CASCADE"), index=True, nullable=False)
    experiencia_id = Column(UUID(as_uuid=True), ForeignKey("catalogo_experiencias.id"), index=True, nullable=False)