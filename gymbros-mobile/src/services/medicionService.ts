import { Medicion } from '../types/medicion';
import { api } from './api';

// Llamadas de mediciones corporales.

// La API las entrega de la más antigua a la más reciente.
export const obtenerMediciones = async () => {
    const { data } = await api.get<Medicion[]>('/mediciones');
    return data;
};
