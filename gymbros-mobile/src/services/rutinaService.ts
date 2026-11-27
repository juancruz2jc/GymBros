import { Rutina } from '../types/rutina';
import { api } from './api';

// Llamadas de rutinas.

// Rutinas del usuario, de la más nueva a la más antigua.
export const obtenerRutinas = async () => {
    const { data } = await api.get<Rutina[]>('/rutinas');
    return data;
};

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