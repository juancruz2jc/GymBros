import uuid
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID, JSONB
# pyrefly: ignore [missing-import]
from sqlalchemy.sql import func
from app.models.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    correo = Column(String(255), unique=True, nullable=False)
    hash_password = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    sexo = Column(String(20), nullable=True)
    altura_cm = Column(Integer, nullable=True)
    foto_url = Column(String(500), nullable=True)
    codigo_gimnasio = Column(String(50), nullable=True)
    tiene_experiencia_previa = Column(Boolean, nullable=True)
    preferencias_notificacion = Column(JSONB, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), index=True, nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    expira_en = Column(DateTime(timezone=True), nullable=False)
    revocado = Column(Boolean, default=False, nullable=False)


class TokenRecuperacion(Base):
    __tablename__ = "tokens_recuperacion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), index=True, nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    expira_en = Column(DateTime(timezone=True), nullable=False)
    usado = Column(Boolean, default=False, nullable=False)


class DispositivoNotificacion(Base):
    __tablename__ = "dispositivos_notificacion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), index=True, nullable=False)
    token_push = Column(String(255), unique=True, nullable=False)
    plataforma = Column(String(50), nullable=False)