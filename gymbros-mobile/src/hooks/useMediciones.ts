import { useCallback, useState } from 'react';
import { getErrorMessage } from '../services/api';
import { eliminarMedicion, listarMediciones } from '../services/medicionService';
import { Medicion } from '../types/medicion';

// useMediciones: historial de mediciones del usuario con sus acciones.
// `mediciones` viene ordenada de la más reciente a la más antigua, así que
// `ultima` es la primera de la lista.
export const useMediciones = () => {
    const [mediciones, setMediciones] = useState<Medicion[]>([]);
    const [cargando, setCargando] = useState(true); // solo la primera carga
    const [error, setError] = useState('');

    // Vuelve a pedir la lista. No pone `cargando` en true para que la pantalla
    // no se vacíe cada vez que se recarga.
    const recargar = useCallback(async () => {
        setError('');
        try {
            const datos = await listarMediciones();
            setMediciones([...datos].reverse()); // la API la manda ascendente
        } catch (e) {
            setError(getErrorMessage(e));
        } finally {
            setCargando(false);
        }
    }, []);

    // Borra en la API y luego la quita de la lista. Si falla, lanza el error
    // para que la pantalla muestre el mensaje.
    const eliminar = useCallback(async (id: string) => {
        await eliminarMedicion(id);
        setMediciones((actuales) => actuales.filter((medicion) => medicion.id !== id));
    }, []);

    return {
        // properties
        mediciones,
        ultima: mediciones.length > 0 ? mediciones[0] : null,
        cargando,
        error,
        // actions
        recargar,
        eliminar,
    };
};
