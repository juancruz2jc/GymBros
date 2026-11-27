// Una serie tal como se envía en POST /sesiones/{id}/series.
export interface SerieRegistrarDatos {
    ejercicio_id: string;
    numero_serie: number; // número de la serie dentro del ejercicio (1, 2, 3...)
    repeticiones_realizadas: number; // 0 = serie fallida
    peso_usado_kg: number; // 0 = peso corporal
    orden: number; // posición de la serie en toda la sesión
}

// Respuesta de POST /sesiones/{id}/series (una por serie guardada).
export interface SerieRegistrada extends SerieRegistrarDatos {
    id: string;
    sesion_id: string;
}

// Una serie dentro del detalle de una sesión finalizada.
export interface SerieDetalle {
    numero_serie: number;
    repeticiones_realizadas: number;
    peso_usado_kg: number;
}

// Las series de un ejercicio dentro del detalle de una sesión finalizada.
export interface EjercicioDetalle {
    ejercicio_id: string;
    nombre_es: string;
    nombre_en: string;
    series: SerieDetalle[];
}

// Respuesta de GET /sesiones/{id}: el item del historial más la nota y las
// series agrupadas por ejercicio. 404 si la sesión sigue activa.
export interface SesionDetalle {
    id: string;
    iniciada_en: string;
    finalizada_en: string;
    duracion_segundos: number | null;
    rutina_id: string | null;
    rutina_nombre: string; // "Entrenamiento libre" si no tiene rutina
    calificacion: number | null;
    nota: string | null;
    ejercicios: EjercicioDetalle[]; // vacía si no tiene series
}

// Cuerpo de PATCH /sesiones/{id}/calificacion.
export interface CalificacionDatos {
    calificacion: number; // entero de 1 a 5
    nota?: string;
}

// Respuesta de PATCH /sesiones/{id}/calificacion.
export interface CalificacionRespuesta {
    id: string;
    calificacion: number;
    nota: string | null;
    finalizada_en: string | null;
}

// Respuesta de GET /ejercicios/{id}/ultimo-registro ("la vez pasada").
// El endpoint responde null si la persona nunca hizo el ejercicio.
export interface UltimoRegistro {
    ejercicio_id: string;
    sesion_id: string;
    fecha: string; // inicio de la sesión donde se hizo, en formato ISO
    numero_serie: number;
    repeticiones_realizadas: number;
    peso_usado_kg: number;
}
