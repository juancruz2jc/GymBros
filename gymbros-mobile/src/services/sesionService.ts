import axios from 'axios';
import {
    CalificacionDatos,
    CalificacionRespuesta,
    SerieRegistrada,
    SerieRegistrarDatos,
    SesionDetalle,
} from '../types/serie';
import { Sesion, SesionHistorialItem, SesionIniciarDatos } from '../types/sesion';
import { api } from './api';

// Llamadas de sesiones de entrenamiento.

// La API responde 404 cuando no hay sesión activa: aquí eso es null, no un error.
export const obtenerSesionActiva = async () => {
    try {
        const { data } = await api.get<Sesion>('/sesiones/activa');
        return data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
            return null;
        }
        throw error;
    }
};

// Sesiones finalizadas, de la más reciente a la más antigua.
export const obtenerHistorial = async (limit = 20, offset = 0) => {
    const { data } = await api.get<SesionHistorialItem[]>('/sesiones', {
        params: { limit, offset },
    });
    return data;
};

export const iniciarSesion = async (datos: SesionIniciarDatos) => {
    const { data } = await api.post<Sesion>('/sesiones', datos);
    return data;
};

// Guarda un lote de series. Si una serie (ejercicio_id + numero_serie) ya
// existía, el backend la actualiza: reenviar el mismo lote no duplica nada.
export const registrarSeries = async (sesionId: string, series: SerieRegistrarDatos[]) => {
    const { data } = await api.post<SerieRegistrada[]>(`/sesiones/${sesionId}/series`, {
        series,
    });
    return data;
};

// Cierra la sesión; la duración la calcula el backend. Sin series hay que
// enviar confirmarSinSeries = true o responde 409.
export const finalizarSesion = async (sesionId: string, confirmarSinSeries = false) => {
    const { data } = await api.post<Sesion>(`/sesiones/${sesionId}/finalizar`, {
        confirmar_sin_series: confirmarSinSeries,
    });
    return data;
};

// Borra una sesión activa junto con sus series (DELETE -> 204).
export const descartarSesion = async (sesionId: string) => {
    await api.delete(`/sesiones/${sesionId}`);
};

// Detalle de una sesión finalizada con sus series por ejercicio.
export const obtenerDetalleSesion = async (sesionId: string) => {
    const { data } = await api.get<SesionDetalle>(`/sesiones/${sesionId}`);
    return data;
};

// Califica (o corrige la calificación de) una sesión finalizada.
export const calificarSesion = async (sesionId: string, datos: CalificacionDatos) => {
    const { data } = await api.patch<CalificacionRespuesta>(
        `/sesiones/${sesionId}/calificacion`,
        datos,
    );
    return data;
};
