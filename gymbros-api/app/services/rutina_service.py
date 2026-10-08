import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.entrenamiento import Rutina, RutinaEjercicio, Ejercicio
from app.schemas.rutina import RutinaCreate, RutinaUpdate

def validar_ejercicios_entrada(db: Session, ejercicios_in):
    """Valida reglas de negocio de los ejercicios antes de insertarlos."""
    if not ejercicios_in:
        return

    # Punto 7: Validar que el orden no se repita
    ordenes = [e.orden for e in ejercicios_in]
    if len(ordenes) != len(set(ordenes)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El orden de los ejercicios no puede repetirse")
    
    # Punto 2: Validar que existan
    ids_entrada = [e.ejercicio_id for e in ejercicios_in]
    ejercicios_db = db.query(Ejercicio).filter(Ejercicio.id.in_(ids_entrada)).all()
    
    if len(ejercicios_db) != len(set(ids_entrada)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Uno o más ejercicios indicados no existen")
        
    # Punto 3: Validar que estén activos
    for ej_db in ejercicios_db:
        if not ej_db.activo:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"El ejercicio {ej_db.nombre_es} está inactivo")


def crear_rutina(db: Session, rutina_in: RutinaCreate, usuario_id: uuid.UUID) -> Rutina:
    validar_ejercicios_entrada(db, rutina_in.ejercicios)

    # 1. Crear el objeto Rutina
    nueva_rutina = Rutina(
        usuario_id=usuario_id,
        nombre=rutina_in.nombre,
        favorita=rutina_in.favorita
    )
    db.add(nueva_rutina)
    db.flush() # Obtiene el ID temporal de la rutina

    # 2. Crear y asociar los ejercicios
    for ej in rutina_in.ejercicios:
        nuevo_ejercicio = RutinaEjercicio(
            rutina_id=nueva_rutina.id,
            ejercicio_id=ej.ejercicio_id,
            orden=ej.orden,
            series_objetivo=ej.series_objetivo,
            repeticiones_objetivo=ej.repeticiones_objetivo,
            descanso_segundos=ej.descanso_segundos
        )
        db.add(nuevo_ejercicio)

    db.commit()
    db.refresh(nueva_rutina)
    return nueva_rutina

def listar_rutinas_usuario(db: Session, usuario_id: uuid.UUID) -> list[Rutina]:
    # Punto 7: order_by agregado
    return db.query(Rutina).filter(Rutina.usuario_id == usuario_id).order_by(Rutina.creado_en.desc()).all()

def obtener_rutina(db: Session, rutina_id: uuid.UUID, usuario_id: uuid.UUID) -> Rutina | None:
    return db.query(Rutina).filter(Rutina.id == rutina_id, Rutina.usuario_id == usuario_id).first()

def actualizar_rutina(db: Session, rutina_id: uuid.UUID, rutina_in: RutinaUpdate, usuario_id: uuid.UUID) -> Rutina | None:
    rutina = obtener_rutina(db, rutina_id, usuario_id)
    if not rutina:
        return None
    
    # Puntos 4 y 6: Actualizar campos
    if rutina_in.nombre is not None:
        rutina.nombre = rutina_in.nombre
    if rutina_in.favorita is not None:
        rutina.favorita = rutina_in.favorita
        
    if rutina_in.ejercicios is not None:
        validar_ejercicios_entrada(db, rutina_in.ejercicios)
        
        # Eliminar ejercicios anteriores y recrearlos (reemplazo total)
        db.query(RutinaEjercicio).filter(RutinaEjercicio.rutina_id == rutina_id).delete()
        
        for ej in rutina_in.ejercicios:
            nuevo_ejercicio = RutinaEjercicio(
                rutina_id=rutina.id,
                ejercicio_id=ej.ejercicio_id,
                orden=ej.orden,
                series_objetivo=ej.series_objetivo,
                repeticiones_objetivo=ej.repeticiones_objetivo,
                descanso_segundos=ej.descanso_segundos
            )
            db.add(nuevo_ejercicio)
            
    db.commit()
    db.refresh(rutina)
    return rutina

def eliminar_rutina(db: Session, rutina_id: uuid.UUID, usuario_id: uuid.UUID) -> bool:
    rutina = obtener_rutina(db, rutina_id, usuario_id)
    if not rutina:
        return False
    
    db.delete(rutina)
    db.commit()
    return True

def duplicar_rutina(db: Session, rutina_id: uuid.UUID, usuario_id: uuid.UUID) -> Rutina | None:
    # 1. Buscar la rutina original (obtener_rutina ya valida que sea del usuario)
    rutina_original = obtener_rutina(db, rutina_id, usuario_id)
    if not rutina_original:
        return None

    # 2. Crear la copia
    nueva_rutina = Rutina(
        usuario_id=usuario_id,
        nombre=f"{rutina_original.nombre} (copia)",
        favorita=False
    )
    db.add(nueva_rutina)
    db.flush() # Guarda temporalmente para obtener el nuevo ID

    # 3. Copiar los ejercicios
    ejercicios_originales = db.query(RutinaEjercicio).filter(
        RutinaEjercicio.rutina_id == rutina_id
    ).all()

    for ej in ejercicios_originales:
        nuevo_ejercicio = RutinaEjercicio(
            rutina_id=nueva_rutina.id,
            ejercicio_id=ej.ejercicio_id,
            orden=ej.orden,
            series_objetivo=ej.series_objetivo,
            repeticiones_objetivo=ej.repeticiones_objetivo,
            descanso_segundos=ej.descanso_segundos
        )
        db.add(nuevo_ejercicio)

    db.commit()
    db.refresh(nueva_rutina)
    return nueva_rutina