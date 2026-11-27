// Formatos de fecha y duración en español.

const DIAS = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

// "Viernes, 25 sep", a partir de una fecha con hora. Se muestra en la hora del
// celular.
export const formatearDiaYMes = (fechaHora: string) => {
    // Se quitan las fracciones de segundo, que no todos los motores leen.
    const fecha = new Date(fechaHora.replace(/\.\d+/, ''));
    return `${DIAS[fecha.getDay()]}, ${fecha.getDate()} ${MESES[fecha.getMonth()]}`;
};

// "10 sep 2026", a partir de "2026-09-10". No se usa new Date(texto) porque lo
// toma como hora UTC y en Colombia mostraría el día anterior.
export const formatearFecha = (fecha: string) => {
    const [anio, mes, dia] = fecha.split('-').map(Number);
    return `${dia} ${MESES[mes - 1]} ${anio}`;
};

// Colombia está en UTC-5 todo el año (no tiene horario de verano).
const DESFASE_COLOMBIA_MS = -5 * 60 * 60 * 1000;

// "Jueves, 26 nov · 6:30 p. m.", a partir de una fecha con hora. Siempre en hora
// de Colombia, sin importar la zona horaria configurada en el celular.
export const formatearFechaHoraColombia = (fechaHora: string) => {
    // Se corre la hora a Colombia y se leen los campos en UTC, así el resultado
    // no depende de la zona del celular.
    const utc = new Date(fechaHora.replace(/\.\d+/, '')).getTime();
    const fecha = new Date(utc + DESFASE_COLOMBIA_MS);
    const horas = fecha.getUTCHours();
    const hora12 = horas % 12 === 0 ? 12 : horas % 12;
    const minutos = String(fecha.getUTCMinutes()).padStart(2, '0');
    const periodo = horas < 12 ? 'a. m.' : 'p. m.';
    return `${DIAS[fecha.getUTCDay()]}, ${fecha.getUTCDate()} ${MESES[fecha.getUTCMonth()]} · ${hora12}:${minutos} ${periodo}`;
};

// "45 min", a partir de segundos. Mínimo 1 min.
export const formatearDuracion = (segundos: number) => {
    return `${Math.max(1, Math.round(segundos / 60))} min`;
};
