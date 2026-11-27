import axios from 'axios';
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
