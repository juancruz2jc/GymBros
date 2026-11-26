import { Rutina } from '../types/rutina';
import { api } from './api';

// Llamadas de rutinas.

// Rutinas del usuario, de la más nueva a la más antigua.
export const obtenerRutinas = async () => {
    const { data } = await api.get<Rutina[]>('/rutinas');
    return data;
};
