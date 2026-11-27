import { Medicion, MedicionComparativa, MedicionDatos } from '../types/medicion';
import { api } from './api';

// Llamadas de mediciones corporales.

// La API las entrega de la más antigua a la más reciente.
export const obtenerMediciones = async () => {
    const { data } = await api.get<Medicion[]>('/mediciones');
    return data;
};

export const obtenerMedicion = async (id: string) => {
    const { data } = await api.get<Medicion>(`/mediciones/${id}`);
    return data;
};

// POST: la fecha va como hora local SIN "Z" ("2026-11-27T12:00:00"). La API la
// toma como hora de Colombia. Con toISOString() saldría en UTC y en la noche
// podría quedar guardada en otro día.
export const crearMedicion = async (datos: MedicionDatos) => {
    const { data } = await api.post<Medicion>('/mediciones', {
        ...datos,
        fecha: `${datos.fecha}T12:00:00`,
    });
    return data;
};

// PUT: la fecha va solo como "AAAA-MM-DD". Solo cambia los campos enviados.
export const editarMedicion = async (id: string, datos: MedicionDatos) => {
    const { data } = await api.put<Medicion>(`/mediciones/${id}`, datos);
    return data;
};

// Compara las mediciones de dos fechas ("AAAA-MM-DD"), en cualquier orden.
// 400 si las fechas son iguales; 404 si alguna no tiene medición (el mensaje
// dice cuál).
export const compararMediciones = async (fecha1: string, fecha2: string) => {
    const { data } = await api.get<MedicionComparativa>('/mediciones/comparar', {
        params: { fecha1, fecha2 },
    });
    return data;
};

// Borra la medición para siempre (la API no tiene papelera).
export const eliminarMedicion = async (id: string) => {
    await api.delete(`/mediciones/${id}`);
};
