import { Rutina } from '../types/rutina';
import { api } from './api';

// Rutinas del usuario, de la más nueva a la más antigua.
export const obtenerRutinas = async (): Promise<Rutina[]> => {
    const { data } = await api.get<Rutina[]>('/rutinas');
    return data;
};

// Alterna el estado de favorita (PATCH /rutinas/{id}/favorita).
export const alternarRutinaFavorita = async (id: string): Promise<Rutina> => {
    const { data } = await api.patch<Rutina>(`/rutinas/${id}/favorita`);
    return data;
};

// Duplica una rutina existente (POST /rutinas/{id}/duplicar -> 201).
export const duplicarRutina = async (id: string): Promise<Rutina> => {
    const { data } = await api.post<Rutina>(`/rutinas/${id}/duplicar`);
    return data;
};

// Elimina una rutina (DELETE /rutinas/{id} -> 204).
export const eliminarRutina = async (id: string): Promise<void> => {
    await api.delete(`/rutinas/${id}`);
};

// Detalle de una rutina por ID (GET /rutinas/{id}).
export const obtenerRutinaPorId = async (id: string): Promise<Rutina> => {
    const { data } = await api.get<Rutina>(`/rutinas/${id}`);
    return data;
};

export interface RutinaEjercicioPayload {
    ejercicio_id: string;
    orden: number;
    series_objetivo: number;
    repeticiones_objetivo: number;
    descanso_segundos: number;
}

export interface CrearActualizarRutinaPayload {
    nombre: string;
    favorita?: boolean;
    ejercicios: RutinaEjercicioPayload[];
}

// Crea una nueva rutina (POST /rutinas -> 201).
export const crearRutina = async (
    payload: CrearActualizarRutinaPayload,
): Promise<Rutina> => {
    const { data } = await api.post<Rutina>('/rutinas', payload);
    return data;
};

// Actualiza una rutina existente (PUT /rutinas/{id}).
export const actualizarRutina = async (
    id: string,
    payload: CrearActualizarRutinaPayload,
): Promise<Rutina> => {
    const { data } = await api.put<Rutina>(`/rutinas/${id}`, payload);
    return data;
};