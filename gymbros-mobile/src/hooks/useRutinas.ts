import { useCallback, useEffect, useState } from 'react';
import { getErrorMessage } from '../services/api';
import {
    alternarRutinaFavorita,
    duplicarRutina,
    eliminarRutina,
    obtenerRutinas,
} from '../services/rutinaService';
import { Rutina } from '../types/rutina';

export const useRutinas = () => {
    const [rutinas, setRutinas] = useState<Rutina[]>([]);
    const [cargando, setCargando] = useState<boolean>(true);
    const [error, setError] = useState<string>('');

    const recargar = useCallback(async () => {
        setCargando(true);
        setError('');
        try {
            const lista = await obtenerRutinas();
            setRutinas(lista);
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setCargando(false);
        }
    }, []);

    useEffect(() => {
        recargar();
    }, [recargar]);

    const alternarFavorita = useCallback(async (id: string) => {
        setRutinas((prev) =>
            prev.map((r) => (r.id === id ? { ...r, favorita: !r.favorita } : r)),
        );
        try {
            const actualizada = await alternarRutinaFavorita(id);
            setRutinas((prev) =>
                prev.map((r) => (r.id === id ? { ...r, ...actualizada } : r)),
            );
        } catch (err) {
            setRutinas((prev) =>
                prev.map((r) => (r.id === id ? { ...r, favorita: !r.favorita } : r)),
            );
            throw new Error(getErrorMessage(err));
        }
    }, []);

    const duplicar = useCallback(async (id: string) => {
        const nueva = await duplicarRutina(id);
        setRutinas((prev) => [nueva, ...prev]);
        return nueva;
    }, []);

    const eliminar = useCallback(async (id: string) => {
        await eliminarRutina(id);
        setRutinas((prev) => prev.filter((r) => r.id !== id));
    }, []);

    return {
        rutinas,
        cargando,
        error,
        recargar,
        alternarFavorita,
        duplicar,
        eliminar,
    };
};