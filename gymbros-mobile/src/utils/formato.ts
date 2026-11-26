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

// "45 min", a partir de segundos. Mínimo 1 min.
export const formatearDuracion = (segundos: number) => {
    return `${Math.max(1, Math.round(segundos / 60))} min`;
};
