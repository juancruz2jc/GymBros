import { useFocusEffect } from '@react-navigation/native';
import axios from 'axios';
import * as Crypto from 'expo-crypto';
import { useCallback, useRef, useState } from 'react';
import { getErrorMessage } from '../services/api';
import { obtenerMediciones } from '../services/medicionService';
import { obtenerRutinas } from '../services/rutinaService';
import { iniciarSesion, obtenerHistorial, obtenerSesionActiva } from '../services/sesionService';
import { Medicion } from '../types/medicion';
import { Rutina } from '../types/rutina';
import { Sesion, SesionHistorialItem } from '../types/sesion';

// useInicio: datos y acciones de la pantalla de Inicio.
export const useInicio = () => {
    const [sesionActiva, setSesionActiva] = useState<Sesion | null>(null);
    const [ultimoEntrenamiento, setUltimoEntrenamiento] = useState<SesionHistorialItem | null>(null);
    const [ultimaMedicion, setUltimaMedicion] = useState<Medicion | null>(null);
    const [rutinas, setRutinas] = useState<Rutina[]>([]);
    const [cargando, setCargando] = useState(true); // solo la primera carga
    const [creando, setCreando] = useState(false);
    const [error, setError] = useState(''); // no se pudieron traer los datos
    const [errorInicio, setErrorInicio] = useState(''); // no se pudo iniciar

    // Clave del intento de iniciar. Se guarda para que un reintento (por ejemplo
    // tras perder la conexión) use la misma y no cree dos sesiones.
    const claveInicio = useRef<string | null>(null);

    const recargar = useCallback(async () => {
        try {
            // Las cuatro peticiones salen a la vez.
            const [activa, historial, mediciones, listaRutinas] = await Promise.all([
                obtenerSesionActiva(),
                obtenerHistorial(1),
                obtenerMediciones(),
                obtenerRutinas(),
            ]);
            setSesionActiva(activa);
            setUltimoEntrenamiento(historial[0] ?? null);
            // Vienen de la más antigua a la más reciente: sirve la última.
            setUltimaMedicion(mediciones[mediciones.length - 1] ?? null);
            setRutinas(listaRutinas);
            setError('');
            setErrorInicio('');
            // Ya se conoce el estado real: el próximo inicio es un intento nuevo.
            claveInicio.current = null;
        } catch (e) {
            setError(getErrorMessage(e));
        } finally {
            setCargando(false);
        }
    }, []);

    // Se ejecuta cada vez que se vuelve a la pestaña, no solo al crearla.
    useFocusEffect(
        useCallback(() => {
            recargar();
        }, [recargar]),
    );

    const rutinaFavorita = rutinas.find((rutina) => rutina.favorita) ?? null;

    // Usuario nuevo: no tiene rutinas ni ha entrenado.
    const esUsuarioNuevo = !sesionActiva && !ultimoEntrenamiento && rutinas.length === 0;

    // Crea la sesión (con la rutina favorita, si hay) y devuelve su id, o null
    // si no se pudo.
    const iniciarEntrenamiento = async () => {
        setCreando(true);
        setErrorInicio('');
        claveInicio.current ??= Crypto.randomUUID();
        try {
            const sesion = await iniciarSesion({
                idempotency_key: claveInicio.current,
                rutina_id: rutinaFavorita?.id,
            });
            claveInicio.current = null;
            return sesion.id;
        } catch (e) {
            if (axios.isAxiosError(e) && e.response?.status === 409) {
                // Ya había una sesión activa: al recargar aparece "Continuar".
                await recargar();
            } else {
                setErrorInicio(getErrorMessage(e));
            }
            return null;
        } finally {
            setCreando(false);
        }
    };

    return {
        // properties
        sesionActiva,
        rutinaFavorita,
        ultimoEntrenamiento,
        ultimaMedicion,
        esUsuarioNuevo,
        cargando,
        creando,
        error,
        errorInicio,
        // actions
        recargar,
        iniciarEntrenamiento,
    };
};
