// Sesión de entrenamiento: respuesta de GET /sesiones/activa y POST /sesiones.
export interface Sesion {
    id: string;
    rutina_id: string | null; // null = entrenamiento libre
    idempotency_key: string;
    iniciada_en: string; // fecha y hora en formato ISO
    finalizada_en: string | null;
    duracion_segundos: number | null;
    calificacion: number | null; // de 1 a 5
    nota: string | null;
}

// Cada elemento de GET /sesiones (historial de sesiones finalizadas).
export interface SesionHistorialItem {
    id: string;
    iniciada_en: string;
    finalizada_en: string;
    duracion_segundos: number | null;
    rutina_id: string | null;
    rutina_nombre: string;
    calificacion: number | null;
}

// Cuerpo de POST /sesiones.
export interface SesionIniciarDatos {
    // Identifica el intento: si se reintenta con la misma, no se duplica.
    idempotency_key: string;
    rutina_id?: string;
}
