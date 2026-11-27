import { useFocusEffect } from '@react-navigation/native';
import { useCallback, useRef, useState } from 'react';
import { getErrorMessage } from '../services/api';
import { obtenerHistorial } from '../services/sesionService';
import { SesionHistorialItem } from '../types/sesion';

const POR_PAGINA = 20;

// useHistorial: sesiones finalizadas, de la más reciente a la más antigua, en
// páginas de 20.
export const useHistorial = () => {
    const [sesiones, setSesiones] = useState<SesionHistorialItem[]>([]);
    const [cargando, setCargando] = useState(true); // solo la primera carga
    const [refrescando, setRefrescando] = useState(false); // gesto de deslizar
    const [cargandoMas, setCargandoMas] = useState(false);
    const [hayMas, setHayMas] = useState(false);
    const [error, setError] = useState('');

    // Cada carga de la primera página invalida las respuestas atrasadas de
    // otras cargas (por ejemplo, "cargar más" que llega después de recargar).
    const version = useRef(0);

    // Trae la primera página. La lista anterior se mantiene en pantalla
    // mientras llega la nueva.
    const recargar = useCallback(async () => {
        const actual = ++version.current;
        try {
            const pagina = await obtenerHistorial(POR_PAGINA, 0);
            if (actual !== version.current) {
                return;
            }
            setSesiones(pagina);
            setHayMas(pagina.length === POR_PAGINA);
            setError('');
        } catch (e) {
            if (actual === version.current) {
                setError(getErrorMessage(e));
            }
        } finally {
            if (actual === version.current) {
                setCargando(false);
                setRefrescando(false);
            }
        }
    }, []);

    // Se recarga cada vez que se vuelve a la pestaña: así aparece el
    // entrenamiento que se acaba de finalizar.
    useFocusEffect(
        useCallback(() => {
            recargar();
        }, [recargar]),
    );

    const refrescar = () => {
        setRefrescando(true);
        recargar();
    };

    // Siguiente página, al llegar al final de la lista.
    const cargarMas = async () => {
        if (!hayMas || cargandoMas || cargando) {
            return;
        }
        const actual = version.current;
        setCargandoMas(true);
        try {
            const pagina = await obtenerHistorial(POR_PAGINA, sesiones.length);
            if (actual !== version.current) {
                return;
            }
            // Se evitan repetidos por si se finalizó una sesión entre páginas.
            setSesiones((prev) => {
                const ids = new Set(prev.map((sesion) => sesion.id));
                return [...prev, ...pagina.filter((sesion) => !ids.has(sesion.id))];
            });
            setHayMas(pagina.length === POR_PAGINA);
        } catch (e) {
            if (actual === version.current) {
                setError(getErrorMessage(e));
            }
        } finally {
            setCargandoMas(false);
        }
    };

    return {
        // properties
        sesiones,
        cargando,
        refrescando,
        cargandoMas,
        hayMas,
        error,
        // actions
        recargar,
        refrescar,
        cargarMas,
    };
};
