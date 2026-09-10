from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Motor de conexión a PostgreSQL. Se crea una sola vez al arrancar: es el pool
# de conexiones, no una conexión.
#
# pool_pre_ping verifica que la conexión siga viva antes de usarla. Sin esto,
# una conexión que el servidor cerró por inactividad falla en la siguiente
# consulta con un error poco claro.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Fábrica de sesiones. Una sesión es la unidad de trabajo: acumula cambios y
# los confirma con commit().
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)
