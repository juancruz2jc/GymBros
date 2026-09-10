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