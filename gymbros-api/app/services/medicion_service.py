"""Mediciones (RF-08, RF-11): historial, IMC (RN-09 a RN-13), edición y borrado.

Lectura (`listar_mediciones`, `obtener_medicion`), edición (`actualizar_medicion`)
y borrado (`eliminar_medicion`), todo restringido al usuario dueño. Nada de
FastAPI aquí; las reglas viven en este módulo.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.medicion import Medicion
from app.models.usuario import Usuario
from app.schemas.medicion import MedicionActualizar, MedicionResponse

# Columnas NOT NULL de `mediciones`: un `null` explícito en el cuerpo del PUT no
# puede vaciarlas, así que se ignora.
_CAMPOS_OBLIGATORIOS = ("peso_kg", "fecha")


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
    """Serializa una fila y le añade el IMC calculado (no es columna)."""
    respuesta = MedicionResponse.model_validate(medicion)
    respuesta.imc = calcular_imc(medicion.peso_kg, altura_cm)
    return respuesta
