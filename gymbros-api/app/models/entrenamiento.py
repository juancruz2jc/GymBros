import uuid
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Numeric, Text, ForeignKey
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID
# pyrefly: ignore [missing-import]
from sqlalchemy.sql import func
from app.models.base import Base


class Ejercicio(Base):
    __tablename__ = "ejercicios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_es = Column(String(100), nullable=False)
    nombre_en = Column(String(100), nullable=False)
    grupo_muscular = Column(String(50), nullable=False)
    equipo = Column(String(50), nullable=False)
    categoria = Column(String(50), nullable=False)
    gif_url = Column(String(500), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)


class Rutina(Base):
    __tablename__ = "rutinas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), index=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    favorita = Column(Boolean, default=False, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())


class RutinaEjercicio(Base):
    __tablename__ = "rutina_ejercicios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rutina_id = Column(UUID(as_uuid=True), ForeignKey("rutinas.id", ondelete="CASCADE"), index=True, nullable=False)
    ejercicio_id = Column(UUID(as_uuid=True), ForeignKey("ejercicios.id", ondelete="RESTRICT"), index=True, nullable=False)
    orden = Column(Integer, nullable=False)
    series_objetivo = Column(Integer, nullable=False)
    repeticiones_objetivo = Column(Integer, nullable=False)
    descanso_segundos = Column(Integer, nullable=False)


class Sesion(Base):
    __tablename__ = "sesiones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), index=True, nullable=False)
    rutina_id = Column(UUID(as_uuid=True), ForeignKey("rutinas.id", ondelete="SET NULL"), index=True, nullable=True)
    idempotency_key = Column(String(255), unique=True, nullable=False)
    iniciada_en = Column(DateTime(timezone=True), nullable=False)
    finalizada_en = Column(DateTime(timezone=True), nullable=True)
    calificacion = Column(Integer, nullable=True)
    nota = Column(Text, nullable=True)
    duracion_segundos = Column(Integer, nullable=False)


class SerieSesion(Base):
    __tablename__ = "series_sesion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sesion_id = Column(UUID(as_uuid=True), ForeignKey("sesiones.id", ondelete="CASCADE"), index=True, nullable=False)
    ejercicio_id = Column(UUID(as_uuid=True), ForeignKey("ejercicios.id", ondelete="RESTRICT"), index=True, nullable=False)
    numero_serie = Column(Integer, nullable=False)
    repeticiones_realizadas = Column(Integer, nullable=False)
    peso_usado_kg = Column(Numeric(5, 2), nullable=False)
    orden = Column(Integer, nullable=False)