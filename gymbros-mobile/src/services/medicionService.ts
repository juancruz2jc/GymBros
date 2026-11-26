import { Medicion } from '../types/medicion';
import { api } from './api';

// Llamadas de mediciones a la API.

// Historial del usuario del token. La API lo devuelve de la más antigua a la
// más reciente (por `fecha`). `desde` y `hasta` son opcionales ("YYYY-MM-DD").
export const listarMediciones = async (desde?: string, hasta?: string) => {
    const { data } = await api.get<Medicion[]>('/mediciones', { params: { desde, hasta } });
    return data;
};

// Borra la medición para siempre (la API no tiene papelera).
export const eliminarMedicion = async (id: string) => {
    await api.delete(`/mediciones/${id}`);
};
