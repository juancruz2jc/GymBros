import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

// useAuth: acceso a la sesión desde cualquier pantalla.
export const useAuth = () => {
    const contexto = useContext(AuthContext);
    if (!contexto) {
        throw new Error('useAuth se debe usar dentro de <AuthProvider>.');
    }
    const { usuario, cargando, login, registrar, logout } = contexto;

    return {
        // properties
        usuario,
        cargando,
        autenticado: usuario !== null,
        // actions
        login,
        registrar,
        logout,
    };
};
