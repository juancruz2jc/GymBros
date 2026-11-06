"""Las migraciones de Alembic y los modelos de SQLAlchemy deben coincidir.

El esquema de pruebas se construye con `alembic upgrade head` (ver conftest).
Si alguien cambia un modelo y olvida generar la migración, la base real
(Supabase, el VPS) quedaría distinta a lo que espera el código: esta prueba lo
detecta antes de llegar a `dev`.

Si falla: `alembic revision --autogenerate -m "..."`, revisar el archivo
generado y subirlo junto con el cambio del modelo.
"""

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from app.models import Base


def test_modelos_y_migraciones_estan_sincronizados(engine):
    with engine.connect() as conexion:
        contexto = MigrationContext.configure(conexion, opts={"compare_type": True})
        diferencias = compare_metadata(contexto, Base.metadata)

    assert diferencias == [], (
        "Los modelos no coinciden con las migraciones. Genera una migración con "
        f"`alembic revision --autogenerate`. Diferencias: {diferencias}"
    )
