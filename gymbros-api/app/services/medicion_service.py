<<<<<<< HEAD
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.medicion import Medicion
from app.models.usuario import Usuario
from app.schemas.medicion import MedicionCrear, IMCRespuesta

# RN-12: Cálculo dinámico de IMC sin persistir en BD (RF-07)
def calcular_imc(peso_kg: float, altura_cm: Optional[float]) -> Optional[IMCRespuesta]:
    if not altura_cm or altura_cm <= 0:
        return None
    
    altura_m = altura_cm / 100.0
    valor_imc = round(peso_kg / (altura_m ** 2), 2)
    
    if valor_imc < 18.5:
        categoria = "Bajo peso"
    elif 18.5 <= valor_imc <= 24.9:
        categoria = "Normal"
    elif 25.0 <= valor_imc <= 29.9:
        categoria = "Sobrepeso"
    else:
        categoria = "Obesidad"
        
    return IMCRespuesta(valor=valor_imc, categoria=categoria)

# RF-06: Registrar medición vinculada al usuario autenticado
def crear_medicion(db: Session, usuario: Usuario, datos: MedicionCrear) -> Tuple[Medicion, Optional[IMCRespuesta]]:
    fecha_actual = datetime.now(timezone.utc)
    fecha_med = datos.fecha.replace(tzinfo=timezone.utc) if datos.fecha.tzinfo is None else datos.fecha
    
    # RN-70: La fecha de medición no puede ser futura
    if fecha_med > fecha_actual:
        raise ValueError("La fecha de medición no puede ser futura")

    nueva_medicion = Medicion(
        usuario_id=usuario.id,
        fecha=datos.fecha,
        peso_kg=datos.peso_kg,
        porcentaje_grasa=datos.porcentaje_grasa,
        masa_muscular_kg=datos.masa_muscular_kg,
        circunf_cintura_cm=datos.circunf_cintura_cm,
        circunf_cadera_cm=datos.circunf_cadera_cm,
        circunf_brazo_cm=datos.circunf_brazo_cm,
        circunf_pierna_cm=datos.circunf_pierna_cm,
        circunf_pecho_cm=datos.circunf_pecho_cm,
    )
    
    db.add(nueva_medicion)
    db.commit()
    db.refresh(nueva_medicion)
    
    imc_calculado = calcular_imc(nueva_medicion.peso_kg, usuario.altura_cm)
    return nueva_medicion, imc_calculado

# RF-10: Detección de inactividad por umbral de 30 días
def obtener_estado_inactividad(db: Session, usuario: Usuario) -> dict:
    # RN-60: Filtro estricto por usuario_id en el WHERE
    stmt = (
        select(Medicion)
        .where(Medicion.usuario_id == usuario.id)
        .order_by(desc(Medicion.fecha))
        .limit(1)
    )
    ultima_medicion = db.scalar(stmt)
    
    if not ultima_medicion:
        return {
            "ultima_medicion": None,
            "dias_desde_ultima_medicion": None,
            "esta_inactivo": False
        }
        
    fecha_ahora = datetime.now(timezone.utc)
    fecha_ult = ultima_medicion.fecha.replace(tzinfo=timezone.utc) if ultima_medicion.fecha.tzinfo is None else ultima_medicion.fecha
    
    dias_transcurridos = (fecha_ahora - fecha_ult).days
    return {
        "ultima_medicion": ultima_medicion.fecha,
        "dias_desde_ultima_medicion": dias_transcurridos,
        "esta_inactivo": dias_transcurridos >= 30
    }
=======
"""Historial de mediciones (RF-08) y cálculo de IMC (RN-09 a RN-13).

Solo lectura: lista las mediciones del usuario autenticado y calcula el IMC de
cada una. Nada de FastAPI aquí; las reglas viven en este módulo.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.medicion import Medicion
from app.models.usuario import Usuario
from app.schemas.medicion import MedicionResponse


def calcular_imc(peso_kg: Decimal | float, altura_cm: int | None) -> float | None:
    """IMC = peso_kg / (altura_m)^2 (RN-12), redondeado a 1 decimal.

    La `altura_cm` que se pasa debe ser la **vigente del usuario**
    (`usuarios.altura_cm`), no la de la fecha de la medición (RN-30): el IMC
    histórico se recalcula siempre con la altura actual.

    RN-09: sin altura registrada (o no positiva) no hay IMC -> devuelve `None`,
    no un 0 ni un error.
    """
    if not altura_cm or altura_cm <= 0:  # RN-09
        return None
    altura_m = Decimal(altura_cm) / Decimal(100)
    imc = Decimal(str(peso_kg)) / (altura_m * altura_m)  # RN-12
    return float(imc.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def listar_mediciones(
    db: Session,
    *,
    usuario: Usuario,
    desde: date | None = None,
    hasta: date | None = None,
) -> list[MedicionResponse]:
    """Historial del `usuario` autenticado, en orden cronológico.

    El `usuario_id` sale del usuario autenticado (del token) y se aplica en el
    `WHERE`, nunca en un filtro posterior: un usuario no puede ver mediciones de
    otro (RF-08).

    RN-34: el orden es por `fecha` de la medición, ascendente, **no** por
    `creado_en`. Alguien puede registrar hoy una medición fechada la semana
    pasada y aun así debe caer en su sitio en la gráfica. `creado_en` solo entra
    como desempate estable cuando dos mediciones comparten `fecha`.

    `desde` y `hasta` son opcionales y ambos inclusivos.
    """
    consulta = select(Medicion).where(Medicion.usuario_id == usuario.id)

    if desde is not None:
        consulta = consulta.where(Medicion.fecha >= desde)
    if hasta is not None:
        consulta = consulta.where(Medicion.fecha <= hasta)

    # RN-34: por fecha de la medición, no por creado_en.
    consulta = consulta.order_by(Medicion.fecha.asc(), Medicion.creado_en.asc())

    filas = db.execute(consulta).scalars().all()
    return [_a_response(fila, usuario.altura_cm) for fila in filas]


def obtener_medicion(
    db: Session,
    *,
    usuario: Usuario,
    medicion_id: UUID,
) -> MedicionResponse | None:
    """Una medición del `usuario` autenticado por su id, o `None`.

    `id` y `usuario_id` van juntos en el `WHERE`: una medición que existe pero es
    de otro usuario devuelve `None` igual que un id inexistente. El endpoint
    traduce ambos casos al mismo 404, sin confirmar ni negar que el id exista
    (no filtrar información: 404, nunca 403).
    """
    consulta = select(Medicion).where(
        Medicion.id == medicion_id,
        Medicion.usuario_id == usuario.id,
    )
    fila = db.execute(consulta).scalar_one_or_none()
    if fila is None:
        return None
    return _a_response(fila, usuario.altura_cm)


def _a_response(medicion: Medicion, altura_cm: int | None) -> MedicionResponse:
    """Serializa una fila y le añade el IMC calculado (no es columna)."""
    respuesta = MedicionResponse.model_validate(medicion)
    respuesta.imc = calcular_imc(medicion.peso_kg, altura_cm)
    return respuesta
>>>>>>> origin/feature/GYM-79-historial-mediciones
