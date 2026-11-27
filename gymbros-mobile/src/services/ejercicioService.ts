import { Ejercicio, FiltrosEjercicio } from '../types/ejercicio';
import { api } from './api';

export const listarEjercicios = async (filtros: FiltrosEjercicio = {}): Promise<Ejercicio[]> => {
    const params: Record<string, string> = {};

    if (filtros.grupo_muscular) {
        params.grupo_muscular = filtros.grupo_muscular;
    }
    if (filtros.equipo) {
        params.equipo = filtros.equipo;
    }
    if (filtros.categoria) {
        params.categoria = filtros.categoria;
    }

    const { data } = await api.get<Ejercicio[]>('/ejercicios', { params });
    return data;
};