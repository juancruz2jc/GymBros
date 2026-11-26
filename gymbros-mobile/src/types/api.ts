// Un error de validación de la API (llega en las respuestas 422).
export interface ErrorValidacion {
    type: string; // tipo de error, p. ej. "missing" o "string_too_short"
    loc: (string | number)[]; // dónde falló, p. ej. ["body", "correo"]
    msg: string; // explicación
    ctx?: Record<string, unknown>; // datos extra, como la longitud mínima
}

// Cuerpo de una respuesta de error. `detail` es un texto cuando se incumple una
// regla de negocio, y una lista cuando falla la validación de los datos.
export interface ApiError {
    detail: string | ErrorValidacion[];
}
