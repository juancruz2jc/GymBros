from datetime import date, datetime
from zoneinfo import ZoneInfo

# Zona horaria oficial del sistema
ZONA_HORARIA_COLOMBIA = ZoneInfo("America/Bogota")


def obtener_fecha_actual_colombia() -> date:
    """Devuelve la fecha actual (date) en la zona horaria de Colombia (UTC-5)."""
    return datetime.now(ZONA_HORARIA_COLOMBIA).date()


def obtener_datetime_actual_colombia() -> datetime:
    """Devuelve el datetime actual con timezone awareness ajustado a Colombia."""
    return datetime.now(ZONA_HORARIA_COLOMBIA)