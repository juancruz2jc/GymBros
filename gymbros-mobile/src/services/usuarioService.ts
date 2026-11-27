import { Usuario, UsuarioActualizar } from '../types/usuario';
import { api } from './api';

// Llamadas sobre el usuario. Para leer el perfil se usa `me` de authService.

// Edición parcial: devuelve el perfil ya actualizado.
export const actualizarPerfil = async (datos: UsuarioActualizar) => {
    const { data } = await api.put<Usuario>('/usuarios/me', datos);
    return data;
};
