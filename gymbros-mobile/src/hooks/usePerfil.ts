import { useCallback, useEffect, useState } from 'react';
import { getErrorMessage } from '../services/api';
import { me } from '../services/authService';
import { actualizarPerfil } from '../services/usuarioService';
import { Usuario, UsuarioActualizar } from '../types/usuario';
import { useAuth } from './useAuth';

// usePerfil: datos y acciones de la pantalla de Perfil.
export const usePerfil = () => {
    const { actualizarUsuario } = useAuth();
    const [perfil, setPerfil] = useState<Usuario | null>(null);
    const [cargando, setCargando] = useState(true);
    const [guardando, setGuardando] = useState(false);
    const [error, setError] = useState(''); // al cargar o al guardar

    // Pide el perfil actual a la API.
    const recargar = useCallback(async () => {
        setCargando(true);
        setError('');
        try {
            setPerfil(await me());
        } catch (e) {
            setError(getErrorMessage(e));
        } finally {
            setCargando(false);
        }
    }, []);

    // Se carga una sola vez: recargar al volver a la pestaña borraría lo que se
    // esté escribiendo.
    useEffect(() => {
        recargar();
    }, [recargar]);

    // Guarda los cambios. Devuelve true si la API los aceptó.
    const actualizar = async (cambios: UsuarioActualizar) => {
        setGuardando(true);
        setError('');
        try {
            const actualizado = await actualizarPerfil(cambios);
            setPerfil(actualizado);
            // El saludo de Inicio usa este usuario: cambia sin recargar.
            actualizarUsuario(actualizado);
            return true;
        } catch (e) {
            setError(getErrorMessage(e));
            return false;
        } finally {
            setGuardando(false);
        }
    };

    return {
        // properties
        perfil,
        cargando,
        guardando,
        error,
        // actions
        recargar,
        actualizar,
    };
};
