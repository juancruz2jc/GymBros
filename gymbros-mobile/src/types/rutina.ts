// Un ejercicio dentro de una rutina. La API no envía su nombre: se cruza con el
// catálogo (GET /ejercicios) usando ejercicio_id.
export interface RutinaEjercicio {
    id: string;
    rutina_id: string;
    ejercicio_id: string;
    orden: number;
    series_objetivo: number;
    repeticiones_objetivo: number;
    descanso_segundos: number;
}

// Rutina: respuesta de /rutinas.
export interface Rutina {
    id: string;
    usuario_id: string;
    nombre: string;
    favorita: boolean;
    creado_en: string | null;
    actualizado_en: string | null;
    ejercicios: RutinaEjercicio[];
}
