"""Servicio del módulo de mediciones corporales (RF-06, RF-07, RF-08, RF-10, RF-11)."""

from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.models.medicion import Medicion
from app.models.usuario import Usuario
from app.schemas.medicion import IMCRespuesta, MedicionActualizar, MedicionCrear, MedicionResponse

# Columnas NOT NULL de `mediciones`: un `null` explícito en el cuerpo del PUT no
# puede vaciarlas, así que se ignora.
_CAMPOS_OBLIGATORIOS = ("peso_kg", "fecha")


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


def actualizar_medicion(
    db: Session,
    *,
    usuario: Usuario,
    medicion_id: UUID,
    datos: MedicionActualizar,
) -> MedicionResponse | None:
    """Edita una medición del `usuario`. `None` si no es suya o no existe.

    RN-08: `id` y `usuario_id` van juntos en el `WHERE`; una medición ajena no se
    encuentra (el endpoint responde 404), sin un `if fila.usuario_id == ...`
    posterior.

    RN-37: nunca se escribe `usuario_id`. El schema `MedicionActualizar` ni lo
    declara; aun así se descarta de forma explícita antes de aplicar los cambios.

    Actualización parcial: solo se escriben los campos presentes en `datos`
    (`exclude_unset`). Un `null` explícito sobre una columna NOT NULL se ignora.
    """
    fila = db.execute(
        select(Medicion).where(
            Medicion.id == medicion_id,
            Medicion.usuario_id == usuario.id,
        )
    ).scalar_one_or_none()
    if fila is None:
        return None

    cambios = datos.model_dump(exclude_unset=True)
    cambios.pop("usuario_id", None)  # RN-37
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
    """Borra definitivamente una medición del `usuario`. `True` si borró algo.

    RN-36: el borrado es físico; no hay papelera ni columna de baja lógica en
    este alcance.

    RN-08: `id` y `usuario_id` van juntos en el `WHERE`. Una medición ajena no se
    borra y la función devuelve `False` (el endpoint responde 404),
    indistinguible de un id inexistente.
    """
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
