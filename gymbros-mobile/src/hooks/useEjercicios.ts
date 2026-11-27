import { useCallback, useEffect, useState } from 'react';
import { getErrorMessage } from '../services/api';
import { listarEjercicios } from '../services/ejercicioService';
import { Ejercicio, FiltrosEjercicio } from '../types/ejercicio';

export const useEjercicios = (filtrosIniciales: FiltrosEjercicio = {}) => {
    const [ejercicios, setEjercicios] = useState<Ejercicio[]>([]);
    const [filtros, setFiltros] = useState<FiltrosEjercicio>(filtrosIniciales);
    const [cargando, setCargando] = useState<boolean>(true);
    const [error, setError] = useState<string>('');

    const cargar = useCallback(async (filtrosActuales: FiltrosEjercicio) => {
        setCargando(true);
        setError('');
        try {
            const lista = await listarEjercicios(filtrosActuales);
            setEjercicios(lista);
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setCargando(false);
        }
    }, []);

    useEffect(() => {
        cargar(filtros);
    }, [cargar, filtros]);

    const filtrar = useCallback((nuevosFiltros: FiltrosEjercicio) => {
        setFiltros(nuevosFiltros);
    }, []);

    const recargar = useCallback(() => {
        cargar(filtros);
    }, [cargar, filtros]);

    return {
        ejercicios,
        filtros,
        cargando,
        error,
        filtrar,
        recargar,
    };
};