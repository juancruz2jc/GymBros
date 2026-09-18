"""Servicio del módulo de mediciones corporales (RF-06, RF-07, RF-08, RF-10, RF-11)."""

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import delete, desc, func, select
from sqlalchemy.orm import Session

from app.models.medicion import Medicion
from app.models.usuario import Usuario
from app.schemas.medicion import (
    DiferenciasMedicion,
    MedicionActualizar,
    MedicionComparativaResponse,
    MedicionCrear,
    MedicionResponse,
)

# H-05: Zona horaria oficial para evitar desfases con UTC
ZONA_COLOMBIA = ZoneInfo("America/Bogota")
_CAMPOS_OBLIGATORIOS = ("peso_kg", "fecha")


# RN-09 a RN-13: Cálculo global de IMC (RF-07)
def calcular_imc(peso_kg: Decimal | float, altura_cm: int | None) -> float | None:
    if not altura_cm or altura_cm <= 0:
        return None
    altura_m = Decimal(altura_cm) / Decimal(100)
    imc = Decimal(str(peso_kg)) / (altura_m * altura_m)
    return float(imc.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


# RF-06: Registrar medición vinculada al usuario autenticado
def crear_medicion(db: Session, usuario: Usuario, datos: MedicionCrear) -> MedicionResponse:
    # H-05: Se calcula "hoy" basado en la hora local de Colombia (UTC-5)
    ahora_co = datetime.now(ZONA_COLOMBIA)

    fecha_med = datos.fecha
    if fecha_med.tzinfo is None:
        fecha_med = fecha_med.replace(tzinfo=ZONA_COLOMBIA)
    else:
        fecha_med = fecha_med.astimezone(ZONA_COLOMBIA)

    # RN-70: La fecha de medición no puede ser futura respecto al día local
    if fecha_med.date() > ahora_co.date():
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
    # H-05: 'hoy' se evalúa con la fecha real de Colombia
    fecha_hoy = datetime.now(ZONA_COLOMBIA).date()

    stmt = (
        select(Medicion)
        .where(
            Medicion.usuario_id == usuario.id,
            Medicion.fecha <= fecha_hoy
        )
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

    fecha_ult = (
        ultima_medicion.fecha
        if isinstance(ultima_medicion.fecha, date) and not isinstance(ultima_medicion.fecha, datetime)
        else ultima_medicion.fecha.date()
    )

    dias_transcurridos = max(0, (fecha_hoy - fecha_ult).days)

    return {
        "ultima_medicion": ultima_medicion.fecha,
        "dias_desde_ultima_medicion": dias_transcurridos,
        "esta_inactivo": dias_transcurridos >= 30
    }


def actualizar_medicion(
    db: Session,
    *,
    usuario: Usuario,
    medicion_id: UUID,
    datos: MedicionActualizar,
) -> MedicionResponse | None:
    fila = db.execute(
        select(Medicion).where(
            Medicion.id == medicion_id,
            Medicion.usuario_id == usuario.id,
        )
    ).scalar_one_or_none()
    if fila is None:
        return None

    cambios = datos.model_dump(exclude_unset=True)
    cambios.pop("usuario_id", None)
    for campo, valor in cambios.items():
        if valor is None and campo in _CAMPOS_OBLIGATORIOS:
            continue
        setattr(fila, campo, valor)

    db.commit()
    db.refresh(fila)
    return _a_response(fila, usuario.altura_cm)


def eliminar_medicion(
    db: Session,
    *,
    usuario: Usuario,
    medicion_id: UUID,
) -> bool:
    resultado = db.execute(
        delete(Medicion).where(
            Medicion.id == medicion_id,
            Medicion.usuario_id == usuario.id,
        )
    )
    db.commit()
    return resultado.rowcount > 0


def _a_response(medicion: Medicion, altura_cm: int | None) -> MedicionResponse:
    respuesta = MedicionResponse.model_validate(medicion)
    respuesta.imc = calcular_imc(medicion.peso_kg, altura_cm)
    return respuesta


# RF-09: Comparar dos mediciones por fecha
def comparar_mediciones(
    db: Session,
    *,
    usuario: Usuario,
    fecha1: date,
    fecha2: date,
) -> Optional[MedicionComparativaResponse]:
    # Consultar ambas mediciones para el usuario
    med1 = db.execute(
        select(Medicion).where(
            Medicion.usuario_id == usuario.id,
            Medicion.fecha == fecha1,
        )
        .order_by(desc(Medicion.creado_en))

    ).first()

    med2 = db.execute(
        select(Medicion).where(
            Medicion.usuario_id == usuario.id,
            Medicion.fecha == fecha2,
        )
        .order_by(desc(Medicion.creado_en))
    ).first()

    if not med1 or not med2:
        return None

    # Ordenar cronológicamente para que la resta sea (reciente - anterior)
    if med1.fecha <= med2.fecha:
        m_anterior, m_reciente = med1, med2
    else:
        m_anterior, m_reciente = med2, med1

    res_anterior = _a_response(m_anterior, usuario.altura_cm)
    res_reciente = _a_response(m_reciente, usuario.altura_cm)

    def _diff(v_rec: float | None, v_ant: float | None) -> float | None:
        if v_rec is None or v_ant is None:
            return None
        return round(v_rec - v_ant, 2)

    diferencias = DiferenciasMedicion(
        peso_kg=_diff(res_reciente.peso_kg, res_anterior.peso_kg),
        porcentaje_grasa=_diff(res_reciente.porcentaje_grasa, res_anterior.porcentaje_grasa),
        masa_muscular_kg=_diff(res_reciente.masa_muscular_kg, res_anterior.masa_muscular_kg),
        circunf_cintura_cm=_diff(res_reciente.circunf_cintura_cm, res_anterior.circunf_cintura_cm),
        circunf_cadera_cm=_diff(res_reciente.circunf_cadera_cm, res_anterior.circunf_cadera_cm),
        circunf_brazo_cm=_diff(res_reciente.circunf_brazo_cm, res_anterior.circunf_brazo_cm),
        circunf_pierna_cm=_diff(res_reciente.circunf_pierna_cm, res_anterior.circunf_pierna_cm),
        circunf_pecho_cm=_diff(res_reciente.circunf_pecho_cm, res_anterior.circunf_pecho_cm),
        imc=_diff(res_reciente.imc, res_anterior.imc),
    )

    return MedicionComparativaResponse(
        medicion_anterior=res_anterior,
        medicion_reciente=res_reciente,
        diferencias=diferencias,
    )