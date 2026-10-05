import uuid
from sqlalchemy.orm import Session
from app.models.entrenamiento import Rutina, RutinaEjercicio
from app.schemas.rutina import RutinaCreate

def crear_rutina(db: Session, rutina_in: RutinaCreate, usuario_id: uuid.UUID) -> Rutina:
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
    return db.query(Rutina).filter(Rutina.usuario_id == usuario_id).all()

def obtener_rutina(db: Session, rutina_id: uuid.UUID, usuario_id: uuid.UUID) -> Rutina | None:
    return db.query(Rutina).filter(Rutina.id == rutina_id, Rutina.usuario_id == usuario_id).first()

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