"""Esquemas del recurso de series de sesión (RF-16).

`SerieCrear` es la entrada para registrar una serie.
`SerieResponse` es la salida (registro creado o actualizado).
`SeriesPayload` acepta una serie individual o un lote (lista) para soporte
offline (RNF-02) y normaliza siempre a lista internamente.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Tope técnico: columna `NUMERIC(5,2)` → máx. 999.99.
# Consistente con la constante usada en el módulo de mediciones.
_MAX_NUMERIC_5_2 = 999.99


# ---------------------------------------------------------
# Validadores reutilizables: rechazo de booleanos
# ---------------------------------------------------------
def _rechazar_bool(valor: object, nombre_campo: str) -> object:
    """Rechaza `True`/`False` en campos que esperan un número.

    Python trata `bool` como subclase de `int`, así que Pydantic
    convierte `true` → `1` sin quejarse. Este validador `mode="before"`
    detecta ese caso antes del parseo y lanza un `ValueError` claro.
    """
    if isinstance(valor, bool):
        raise ValueError(
            f"El campo '{nombre_campo}' debe ser numérico, no booleano."
        )
    return valor


# ---------------------------------------------------------
# Entrada: Registrar serie (RF-16)
# ---------------------------------------------------------
class SerieCrear(BaseModel):
    """Datos de una serie individual dentro de una sesión.

    Validaciones:
    - `ejercicio_id`: UUID del ejercicio (obligatorio).
    - `numero_serie`: número de la serie dentro del ejercicio (≥ 1).
    - `repeticiones_realizadas`: entero > 0.
    - `peso_usado_kg`: float ≥ 0 (permite 0 para ejercicios con peso corporal);
      tope en 999.99 por capacidad de la columna `NUMERIC(5,2)`.
    - `orden`: posición de la serie en la sesión (≥ 1).

    Los validadores `mode="before"` rechazan `bool` en campos numéricos
    para evitar que Pydantic convierta `true`→`1` de forma silenciosa.
    """

    ejercicio_id: UUID = Field(
        ..., description="ID del ejercicio del catálogo"
    )
    numero_serie: int = Field(
        ..., gt=0, description="Número de la serie dentro del ejercicio (≥ 1)"
    )
    # RN-45: 0 es válido (serie fallida / no completada), no un error.
    repeticiones_realizadas: int = Field(
        ..., ge=0, description="Cantidad de repeticiones realizadas (≥ 0; 0 = serie fallida)"
    )
    peso_usado_kg: float = Field(
        ...,
        ge=0,
        le=_MAX_NUMERIC_5_2,
        description="Peso usado en kg (≥ 0, permite 0 para peso corporal)",
    )
    orden: int = Field(
        ..., gt=0, description="Orden de la serie dentro de la sesión (≥ 1)"
    )

    # --- Rechazo de booleanos antes del parseo ---
    @field_validator("numero_serie", mode="before")
    @classmethod
    def _no_bool_numero_serie(cls, v: object) -> object:
        return _rechazar_bool(v, "numero_serie")

    @field_validator("repeticiones_realizadas", mode="before")
    @classmethod
    def _no_bool_repeticiones(cls, v: object) -> object:
        return _rechazar_bool(v, "repeticiones_realizadas")

    @field_validator("peso_usado_kg", mode="before")
    @classmethod
    def _no_bool_peso(cls, v: object) -> object:
        return _rechazar_bool(v, "peso_usado_kg")

    @field_validator("orden", mode="before")
    @classmethod
    def _no_bool_orden(cls, v: object) -> object:
        return _rechazar_bool(v, "orden")


# ---------------------------------------------------------
# Salida: Respuesta de serie registrada
# ---------------------------------------------------------
class SerieResponse(BaseModel):
    """Una serie tal como se devuelve en la respuesta del endpoint."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sesion_id: UUID
    ejercicio_id: UUID
    numero_serie: int
    repeticiones_realizadas: int
    peso_usado_kg: float
    orden: int


# ---------------------------------------------------------
# Payload flexible: una serie o un lote (RF-16 + RNF-02)
# ---------------------------------------------------------
class SeriesPayload(BaseModel):
    """Acepta una sola serie o una lista de series.

    El campo `series` se normaliza siempre a `list[SerieCrear]`:
    - Si llega un dict → se envuelve en una lista de un solo elemento.
    - Si llega una lista → se usa tal cual.

    Esto permite al cliente offline enviar un lote completo en una sola
    petición, y al cliente online enviar serie por serie.
    """

    series: list[SerieCrear] = Field(
        ...,
        min_length=1,
        description="Una serie o lista de series a registrar",
    )

    @field_validator("series", mode="before")
    @classmethod
    def _normalizar_a_lista(cls, v: object) -> object:
        """Si el cliente envía un solo objeto, lo convierte a lista."""
        if isinstance(v, dict):
            return [v]
        return v

    @field_validator("series")
    @classmethod
    def _sin_series_repetidas(cls, series: list[SerieCrear]) -> list[SerieCrear]:
        """La misma `(ejercicio_id, numero_serie)` dos veces en un lote es
        ambigua (¿cuál vale?) y además chocaba con la restricción única al
        guardar (500). Se rechaza con 422."""
        claves = [(s.ejercicio_id, s.numero_serie) for s in series]
        if len(claves) != len(set(claves)):
            raise ValueError(
                "El lote repite la misma serie (ejercicio_id y numero_serie)."
            )
        return series
