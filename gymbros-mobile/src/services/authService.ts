import { LoginDatos, RegistroDatos, Tokens } from '../types/auth';
import { Usuario } from '../types/usuario';
import { api, esperarRefresh, refrescarSesion } from './api';
import { borrarTokens, guardarTokens, leerTokens } from './tokenStorage';

// Llamadas de autenticación a la API.

export const login = async (datos: LoginDatos) => {
    const { data } = await api.post<Tokens>('/auth/login', datos);
    await guardarTokens(data);
};

// El registro deja la sesión iniciada: devuelve los mismos tokens que el login.
export const registro = async (datos: RegistroDatos) => {
    const { data } = await api.post<Tokens>('/auth/registro', datos);
    await guardarTokens(data);
};

// Usa el mismo refresh del interceptor, para que nunca haya dos a la vez.
export const refresh = () => refrescarSesion();

export const logout = async () => {
    // Si hay un refresh en curso se espera, para revocar el token más nuevo.
    await esperarRefresh();
    const tokens = await leerTokens();
    // Primero se borran en el dispositivo: la sesión se cierra aunque no haya red.
    await borrarTokens();
    if (!tokens) {
        return;
    }
    try {
        await api.post('/auth/logout', { refresh_token: tokens.refresh_token });
    } catch {
        // Si el servidor no responde, el token queda vivo allá hasta que expire,
        // pero ya no existe en este dispositivo.
    }
};

// Perfil del usuario dueño del token.
export const me = async () => {
    const { data } = await api.get<Usuario>('/usuarios/me');
    return data;
};
