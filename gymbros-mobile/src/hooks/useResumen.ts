import { useCallback, useEffect, useState } from 'react';
import { getErrorMessage } from '../services/api';
import { calificarSesion, obtenerDetalleSesion } from '../services/sesionService';
import { EjercicioDetalle, SesionDetalle } from '../types/serie';

// Qué se muestra después de la calificación: el formulario, "Calificación
// guardada" o "Sesión guardada sin calificación".
export type EstadoResumen = 'calificando' | 'guardada' | 'omitida';

// Volumen total: suma de repeticiones x peso de todas las series.
export const calcularVolumen = (ejercicios: EjercicioDetalle[]) =>
    ejercicios.reduce(
        (total, ejercicio) =>
            total +
            ejercicio.series.reduce(
                (suma, serie) => suma + serie.repeticiones_realizadas * serie.peso_usado_kg,
                0,
            ),
        0,
    );

export const contarSeries = (ejercicios: EjercicioDetalle[]) =>
    ejercicios.reduce((total, ejercicio) => total + ejercicio.series.length, 0);

// useResumen: datos y acciones de la pantalla de resumen de la sesión.
export const useResumen = (sesionId: string) => {
    const [sesion, setSesion] = useState<SesionDetalle | null>(null);
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState(''); // no se pudo cargar
    const [guardando, setGuardando] = useState(false);
    const [errorGuardar, setErrorGuardar] = useState('');
    const [estado, setEstado] = useState<EstadoResumen>('calificando');

    const recargar = useCallback(async () => {
        setCargando(true);
        setError('');
        try {
            setSesion(await obtenerDetalleSesion(sesionId));
        } catch (e) {
            setError(getErrorMessage(e));
        } finally {
            setCargando(false);
        }
    }, [sesionId]);

    useEffect(() => {
        recargar();
    }, [recargar]);

    // Guarda la calificación (1 a 5) y la nota, si se escribió.
    const calificar = async (calificacion: number, nota: string) => {
        setGuardando(true);
        setErrorGuardar('');
        try {
            const notaLimpia = nota.trim();
            const respuesta = await calificarSesion(sesionId, {
                calificacion,
                ...(notaLimpia !== '' && { nota: notaLimpia }),
            });
            setSesion((actual) =>
                actual
                    ? { ...actual, calificacion: respuesta.calificacion, nota: respuesta.nota }
                    : actual,
            );
            setEstado('guardada');
        } catch (e) {
            setErrorGuardar(getErrorMessage(e));
        } finally {
            setGuardando(false);
        }
    };

    // Calificar es opcional (RN-48): la sesión ya quedó guardada al finalizar.
    const omitir = () => {
        setErrorGuardar('');
        setEstado('omitida');
    };

    const ejercicios = sesion?.ejercicios ?? [];

    return {
        // properties
        sesion,
        volumenTotal: calcularVolumen(ejercicios),
        totalSeries: contarSeries(ejercicios),
        cargando,
        error,
        guardando,
        errorGuardar,
        estado,
        // actions
        recargar,
        calificar,
        omitir,
    };
};
