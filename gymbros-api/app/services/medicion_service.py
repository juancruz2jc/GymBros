"""Servicio del módulo de mediciones corporales (RF-06, RF-07, RF-08, RF-10)."""

from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.models.medicion import Medicion
from app.models.usuario import Usuario
from app.schemas.medicion import MedicionCrear, MedicionResponse, IMCRespuesta

# RN-09 a RN-13: Cálculo global de IMC (RF-07)
def calcular_imc(peso_kg: Decimal | float, altura_cm: int | None) -> float | None:
    """IMC = peso_kg / (altura_m)^2 (RN-12), redondeado a 1 decimal."""
    if not altura_cm or altura_cm <= 0:  # RN-09
        return None
    altura_m = Decimal(altura_cm) / Decimal(100)
    imc = Decimal(str(peso_kg)) / (altura_m * altura_m)  # RN-12
    return float(imc.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

# RF-06: Registrar medición vinculada al usuario autenticado
def crear_medicion(db: Session, usuario: Usuario, datos: MedicionCrear) -> MedicionResponse:
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
    
    return _a_response(nueva_medicion, usuario.altura_cm)

# RF-08: Historial y consulta de mediciones (GYM-79)
def listar_mediciones(
    db: Session,
    *,
    usuario: Usuario,
    desde: date | None = None,
    hasta: date | None = None,
) -> List[MedicionResponse]:
    consulta = select(Medicion).where(Medicion.usuario_id == usuario.id)

    if desde is not None:
        consulta = consulta.where(Medicion.fecha >= desde)
    if hasta is not None:
        consulta = consulta.where(Medicion.fecha <= hasta)

    consulta = consulta.order_by(Medicion.fecha.asc(), Medicion.creado_en.asc())
    filas = db.execute(consulta).scalars().all()
    return [_a_response(fila, usuario.altura_cm) for fila in filas]

def obtener_medicion(
    db: Session,
    *,
    usuario: Usuario,
    medicion_id: UUID,
) -> Optional[MedicionResponse]:
    consulta = select(Medicion).where(
        Medicion.id == medicion_id,
        Medicion.usuario_id == usuario.id,
    )
    fila = db.execute(consulta).scalar_one_or_none()
    if fila is None:
        return None
    return _a_response(fila, usuario.altura_cm)

# RF-10: Detección de inactividad por umbral de 30 días
def obtener_estado_inactividad(db: Session, usuario: Usuario) -> dict:
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

# Auxiliar de respuesta
def _a_response(medicion: Medicion, altura_cm: int | None) -> MedicionResponse:
    respuesta = MedicionResponse.model_validate(medicion)
    respuesta.imc = calcular_imc(medicion.peso_kg, altura_cm)
    return respuesta