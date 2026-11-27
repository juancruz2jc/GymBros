import axios from 'axios';
import * as Crypto from 'expo-crypto';
import { useCallback, useEffect, useRef, useState } from 'react';
import { getErrorMessage } from '../services/api';
import { obtenerUltimoRegistro } from '../services/ejercicioService';
import { obtenerRutinaPorId } from '../services/rutinaService';
import {
    descartarSesion,
    finalizarSesion,
    obtenerSesionActiva,
    registrarSeries,
} from '../services/sesionService';
import { SerieRegistrarDatos, UltimoRegistro } from '../types/serie';
import { Sesion } from '../types/sesion';

// Un ejercicio de la sesión. Los que vienen de la rutina traen su objetivo; los
// que se agregan desde el catálogo (entrenamiento libre) no.
export interface EjercicioSesion {
    ejercicio_id: string;
    series_objetivo: number | null;
    repeticiones_objetivo: number | null;
    descanso_segundos: number | null;
}

// Una serie registrada en el celular. Se envía al backend al finalizar.
export interface SerieLocal {
    clave: string; // id local, para la lista y para borrarla
    ejercicio_id: string;
    repeticiones_realizadas: number;
    peso_usado_kg: number;
}

// Resultado de finalizar: 'ok' (ir al Resumen), 'sinSeries' (hay que pedir
// confirmación) o 'error' (el mensaje queda en errorAccion).
export type ResultadoFinalizar = 'ok' | 'sinSeries' | 'error';

// 409 = la sesión ya estaba finalizada (por un intento anterior cuya respuesta
// se perdió, o desde otro dispositivo).
const esConflicto = (error: unknown) =>
    axios.isAxiosError(error) && error.response?.status === 409;

// Convierte las series locales en el lote que espera la API. numero_serie se
// cuenta por ejercicio y orden en toda la sesión. Con las mismas series siempre
// sale el mismo lote, así que reintentar no duplica (upsert en el backend).
export const construirLote = (series: SerieLocal[]): SerieRegistrarDatos[] => {
    const contador: Record<string, number> = {};
    return series.map((serie, indice) => {
        contador[serie.ejercicio_id] = (contador[serie.ejercicio_id] ?? 0) + 1;
        return {
            ejercicio_id: serie.ejercicio_id,
            numero_serie: contador[serie.ejercicio_id],
            repeticiones_realizadas: serie.repeticiones_realizadas,
            peso_usado_kg: serie.peso_usado_kg,
            orden: indice + 1,
        };
    });
};

// Lee las fechas de la API. Se quitan las fracciones de segundo, que no todos
// los motores leen (igual que en utils/formato.ts).
const leerFecha = (fechaHora: string) => new Date(fechaHora.replace(/\.\d+/, '')).getTime();

// useSesionActiva: datos y acciones de la pantalla de entrenamiento activo.
// Las series viven en este estado y se envían en un solo lote al finalizar.
export const useSesionActiva = (sesionId: string) => {
    const [sesion, setSesion] = useState<Sesion | null>(null);
    const [nombreRutina, setNombreRutina] = useState('Entrenamiento libre');
    const [ejercicios, setEjercicios] = useState<EjercicioSesion[]>([]);
    const [series, setSeries] = useState<SerieLocal[]>([]);
    // undefined = aún no se ha pedido; null = nunca hizo el ejercicio.
    const [ultimos, setUltimos] = useState<Record<string, UltimoRegistro | null>>({});
    const [tiempo, setTiempo] = useState(0); // segundos desde el inicio
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState(''); // no se pudo cargar la sesión
    const [noActiva, setNoActiva] = useState(false); // ya se finalizó o descartó
    const [finalizando, setFinalizando] = useState(false);
    const [descartando, setDescartando] = useState(false);
    const [errorAccion, setErrorAccion] = useState(''); // falló finalizar o descartar

    // true cuando el lote ya llegó al backend. Desde ahí no se permite borrar
    // series: la API no tiene cómo eliminarlas y quedarían guardadas.
    const loteEnviado = useRef(false);
    // Ejercicios cuyo "la vez pasada" ya se pidió, para no repetir la petición.
    const ultimosPedidos = useRef(new Set<string>());

    const recargar = useCallback(async () => {
        setCargando(true);
        setError('');
        try {
            const activa = await obtenerSesionActiva();
            // Si no hay sesión activa, o es otra, esta ya se cerró.
            if (!activa || activa.id !== sesionId) {
                setSesion(null);
                setNoActiva(true);
                return;
            }
            setSesion(activa);
            setNoActiva(false);

            if (activa.rutina_id) {
                try {
                    const rutina = await obtenerRutinaPorId(activa.rutina_id);
                    setNombreRutina(rutina.nombre);
                    setEjercicios(
                        [...rutina.ejercicios]
                            .sort((a, b) => a.orden - b.orden)
                            .map((item) => ({
                                ejercicio_id: item.ejercicio_id,
                                series_objetivo: item.series_objetivo,
                                repeticiones_objetivo: item.repeticiones_objetivo,
                                descanso_segundos: item.descanso_segundos,
                            })),
                    );
                } catch (e) {
                    // Si borraron la rutina, se sigue como entrenamiento libre.
                    if (!(axios.isAxiosError(e) && e.response?.status === 404)) {
                        throw e;
                    }
                }
            }
        } catch (e) {
            setError(getErrorMessage(e));
        } finally {
            setCargando(false);
        }
    }, [sesionId]);

    useEffect(() => {
        recargar();
    }, [recargar]);

    // Cronómetro: cuenta desde la hora de inicio que guardó el backend, así
    // sigue bien aunque la app se haya cerrado. Se limpia al salir.
    useEffect(() => {
        if (!sesion) {
            return;
        }
        const inicio = leerFecha(sesion.iniciada_en);
        const actualizar = () => {
            // Si el reloj del celular va atrasado no se muestran negativos.
            setTiempo(Math.max(0, Math.floor((Date.now() - inicio) / 1000)));
        };
        actualizar();
        const intervalo = setInterval(actualizar, 1000);
        return () => clearInterval(intervalo);
    }, [sesion]);

    // "La vez pasada" de cada ejercicio, pedido una sola vez. Si falla, la
    // pantalla simplemente no lo muestra.
    useEffect(() => {
        ejercicios.forEach(({ ejercicio_id }) => {
            if (ultimosPedidos.current.has(ejercicio_id)) {
                return;
            }
            ultimosPedidos.current.add(ejercicio_id);
            obtenerUltimoRegistro(ejercicio_id)
                .then((registro) => setUltimos((prev) => ({ ...prev, [ejercicio_id]: registro })))
                .catch(() => ultimosPedidos.current.delete(ejercicio_id));
        });
    }, [ejercicios]);

    // Agrega un ejercicio del catálogo (si no está) y devuelve su posición.
    const agregarEjercicio = (ejercicioId: string) => {
        const existente = ejercicios.findIndex((e) => e.ejercicio_id === ejercicioId);
        if (existente !== -1) {
            return existente;
        }
        setEjercicios((prev) => [
            ...prev,
            {
                ejercicio_id: ejercicioId,
                series_objetivo: null,
                repeticiones_objetivo: null,
                descanso_segundos: null,
            },
        ]);
        return ejercicios.length;
    };

    const agregarSerie = (ejercicioId: string, repeticiones: number, pesoKg: number) => {
        setErrorAccion('');
        setSeries((prev) => [
            ...prev,
            {
                clave: Crypto.randomUUID(),
                ejercicio_id: ejercicioId,
                repeticiones_realizadas: repeticiones,
                peso_usado_kg: pesoKg,
            },
        ]);
    };

    // Devuelve false si ya no se puede borrar (el lote ya está en el backend).
    const eliminarSerie = (clave: string) => {
        if (loteEnviado.current) {
            return false;
        }
        setSeries((prev) => prev.filter((serie) => serie.clave !== clave));
        return true;
    };

    // Envía el lote y cierra la sesión. Se puede reintentar sin duplicar: el
    // lote se reenvía igual (upsert) y un 409 significa que ya quedó cerrada.
    const finalizar = async (confirmarSinSeries = false): Promise<ResultadoFinalizar> => {
        const sinSeries = series.length === 0;
        if (sinSeries && !confirmarSinSeries) {
            return 'sinSeries';
        }

        setFinalizando(true);
        setErrorAccion('');
        try {
            if (!sinSeries) {
                try {
                    await registrarSeries(sesionId, construirLote(series));
                    loteEnviado.current = true;
                } catch (e) {
                    if (esConflicto(e)) {
                        return 'ok';
                    }
                    throw e;
                }
            }
            try {
                await finalizarSesion(sesionId, sinSeries);
            } catch (e) {
                // Con series recién guardadas, el único 409 posible es "ya
                // estaba finalizada": el intento anterior sí llegó.
                if (esConflicto(e)) {
                    return 'ok';
                }
                throw e;
            }
            return 'ok';
        } catch (e) {
            setErrorAccion(getErrorMessage(e));
            return 'error';
        } finally {
            setFinalizando(false);
        }
    };

    // Borra la sesión y sus series. Devuelve true si ya no existe.
    const descartar = async () => {
        setDescartando(true);
        setErrorAccion('');
        try {
            await descartarSesion(sesionId);
            return true;
        } catch (e) {
            // 404: ya no existía, que es justo lo que se quería.
            if (axios.isAxiosError(e) && e.response?.status === 404) {
                return true;
            }
            setErrorAccion(getErrorMessage(e));
            return false;
        } finally {
            setDescartando(false);
        }
    };

    return {
        // properties
        sesion,
        nombreRutina,
        ejercicios,
        series,
        ultimos,
        tiempo,
        cargando,
        error,
        noActiva,
        finalizando,
        descartando,
        errorAccion,
        // actions
        recargar,
        agregarEjercicio,
        agregarSerie,
        eliminarSerie,
        finalizar,
        descartar,
    };
};
