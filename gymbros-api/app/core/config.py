from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valor de muestra que vive en `.env.example`. Si llega hasta aquí es que alguien
# copió el archivo, no cambió el secreto y arrancó con el de ejemplo.
# IMPORTANTE: este string debe ser idéntico al del `.env.example`. Si se edita
# uno de los dos, la validación deja de dispararse sin avisar.
JWT_SECRET_DE_EJEMPLO = "cambiar-por-un-valor-aleatorio"

# Longitud mínima aceptable para el secreto de firma de los JWT.
JWT_SECRET_LONGITUD_MINIMA = 32


class Settings(BaseSettings):
    """Parámetros de arranque del servicio.

    Un campo por variable de entorno. Los campos sin valor por defecto son
    obligatorios; si faltan, la app no arranca. El tipo declarado se aplica: p.
    ej. `ACCESS_TOKEN_MINUTOS: int` convierte el texto del `.env` a entero y
    falla si no es un número.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Obligatorias (sin valor por defecto) ---
    DATABASE_URL: str
    JWT_SECRET: str

    # --- Opcionales (con valor por defecto) ---
    # Los defaults deben coincidir con los del `.env.example`.
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTOS: int = 15
    REFRESH_TOKEN_DIAS: int = 30
    RECUPERACION_TOKEN_MINUTOS: int = 60  # RN-27

    @field_validator("JWT_SECRET")
    @classmethod
    def _rechazar_secreto_de_ejemplo(cls, valor: str) -> str:
        if valor == JWT_SECRET_DE_EJEMPLO:
            raise ValueError(
                "JWT_SECRET tiene el valor de ejemplo de .env.example. Genera uno "
                'propio, p. ej.: python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )
        if len(valor) < JWT_SECRET_LONGITUD_MINIMA:
            raise ValueError(
                f"JWT_SECRET debe tener al menos {JWT_SECRET_LONGITUD_MINIMA} caracteres."
            )
        return valor


# Instancia única, creada al importar el módulo. La configuración se lee una vez
# al arrancar, no en cada petición.
#
# El `type: ignore` es porque el analizador estático ve una clase con campos
# obligatorios y cree que faltan argumentos en la llamada. En BaseSettings esos
# valores no se pasan como argumentos: se leen del entorno y del `.env`.
settings = Settings()  # type: ignore[call-arg]