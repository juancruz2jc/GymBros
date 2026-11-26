import { createContext, ReactNode, useEffect, useState } from 'react';
import { alTerminarSesion } from '../services/api';
import * as authService from '../services/authService';
import { leerTokens } from '../services/tokenStorage';
import { LoginDatos, RegistroDatos } from '../types/auth';
import { Usuario } from '../types/usuario';

interface AuthContextValue {
    usuario: Usuario | null;
    cargando: boolean;
    login: (datos: LoginDatos) => Promise<void>;
    registrar: (datos: RegistroDatos) => Promise<void>;
    logout: () => Promise<void>;
    actualizarUsuario: (usuario: Usuario) => void;
}

// Las pantallas no usan este contexto directamente, sino el hook useAuth.
export const AuthContext = createContext<AuthContextValue | null>(null);

interface Props {
    children: ReactNode;
}

// AuthProvider: guarda quién inició sesión y lo comparte con toda la app.
// Props: children (la app que puede usar useAuth).
export const AuthProvider = ({ children }: Props) => {
    const [usuario, setUsuario] = useState<Usuario | null>(null);
    // Solo indica la carga inicial. El envío de un formulario lo controla cada
    // pantalla; si no, Login se desmontaría mientras se envía.
    const [cargando, setCargando] = useState(true);

    // Se ejecuta una vez, al abrir la app.
    useEffect(() => {
        // Si api.ts detecta que la sesión ya no sirve, se vuelve a Login.
        alTerminarSesion(() => setUsuario(null));

        const restaurarSesion = async () => {
            try {
                if (await leerTokens()) {
                    await authService.refresh(); // par de tokens nuevo
                    setUsuario(await authService.me());
                }
            } catch {
                // Se muestra Login. Aquí no se borra nada: si el refresh dio
                // 401, api.ts ya borró los tokens; con cualquier otro fallo
                // (sin internet, servidor caído) se conservan para reintentar
                // la próxima vez que se abra la app.
            } finally {
                setCargando(false);
            }
        };

        restaurarSesion();
    }, []);

    // login y registrar dejan pasar los errores para que la pantalla los muestre.
    const login = async (datos: LoginDatos) => {
        await authService.login(datos);
        setUsuario(await authService.me());
    };

    const registrar = async (datos: RegistroDatos) => {
        await authService.registro(datos);
        setUsuario(await authService.me());
    };

    const logout = async () => {
        await authService.logout();
        setUsuario(null);
    };

    // Reemplaza los datos del usuario tras editar el perfil, para que toda la
    // app los vea sin volver a pedirlos.
    const actualizarUsuario = (nuevo: Usuario) => {
        // Si ya se cerró la sesión, una respuesta atrasada no la vuelve a abrir.
        setUsuario((actual) => (actual ? nuevo : null));
    };

    return (
        <AuthContext.Provider
            value={{ usuario, cargando, login, registrar, logout, actualizarUsuario }}
        >
            {children}
        </AuthContext.Provider>
    );
};
