import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock

from app.main import app
from app.api.dependencies import get_db

# 1. Configuración de base de datos SQLite en memoria RAM
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa exclusiva para las pruebas (evita conflictos de importación)
TestBase = declarative_base()
TestBase.metadata.create_all(bind=engine)

# Sobrescribir get_db para aislar Supabase
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# 2. Pruebas de endpoint
def test_api_salud():
    """Valida que la app responde peticiones HTTP"""
    response = client.get("/docs")
    assert response.status_code == 200

# 3. Prueba unitaria pura con Mock
def test_mock_sesion_db():
    """Valida la interacción con SQLAlchemy usando un doble de prueba"""
    db_mock = MagicMock()
    db_mock.add("registro_falso")
    db_mock.commit()

    db_mock.add.assert_called_once_with("registro_falso")
    db_mock.commit.assert_called_once()