import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { ApiError, ErrorValidacion } from '../types/api';
import { Tokens } from '../types/auth';
import { borrarTokens, guardarTokens, leerTokens } from './tokenStorage';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL;
const TIEMPO_MAXIMO_MS = 15000;

// Cliente HTTP de la app. Todas las peticiones a la API salen de aquí.
export const api = axios.create({ baseURL: BASE_URL, timeout: TIEMPO_MAXIMO_MS });

// ---------------------------------------------------------------------------
// Aviso de sesión terminada
// ---------------------------------------------------------------------------
// Este archivo no conoce React. AuthContext le entrega la función que debe
// llamar cuando la sesión ya no sirve, para volver a la pantalla de Login.
let avisarSesionTerminada = () => {};

export const alTerminarSesion = (accion: () => void) => {
    avisarSesionTerminada = accion;
};

// ---------------------------------------------------------------------------
// Antes de cada petición: agregar el access token
// ---------------------------------------------------------------------------
api.interceptors.request.use(async (config) => {
    const tokens = await leerTokens();
    if (tokens) {
        config.headers.Authorization = `Bearer ${tokens.access_token}`;
    }
    return config;
});

// ---------------------------------------------------------------------------
// Refresh: uno solo a la vez
// ---------------------------------------------------------------------------
// La API revoca el refresh token apenas se usa. Si dos peticiones renovaran al
// mismo tiempo con el mismo token, la segunda recibiría 401 y se perdería la
// sesión. Por eso la primera crea la promesa y las demás esperan esa misma.
let refreshEnCurso: Promise<Tokens> | null = null;

const pedirTokensNuevos = async () => {
    const guardados = await leerTokens();
    if (!guardados) {
        throw new Error('No hay una sesión guardada.');
    }

    try {
        // Se usa axios y no `api`: así esta petición no pasa por los
        // interceptores y un 401 aquí no dispara otro refresh.
        const { data } = await axios.post<Tokens>(
            `${BASE_URL}/auth/refresh`,
            { refresh_token: guardados.refresh_token },
            { timeout: TIEMPO_MAXIMO_MS },
        );

        // Si mientras tanto se cerró la sesión, no se vuelven a guardar tokens.
        const actuales = await leerTokens();
        if (actuales?.refresh_token !== guardados.refresh_token) {
            throw new Error('La sesión cambió mientras se renovaba.');
        }

        await guardarTokens(data);
        return data;
    } catch (error) {
        // Los tokens se borran SOLO con un 401, que significa que el refresh ya
        // no sirve (expiró o fue revocado). Sin internet, con timeout o con un
        // error 500 el token puede seguir siendo válido: se conserva para
        // reintentar la próxima vez, sin obligar a escribir la contraseña.
        if (axios.isAxiosError(error) && error.response?.status === 401) {
            await borrarTokens();
            avisarSesionTerminada();
        }
        throw error;
    }
};

export const refrescarSesion = () => {
    if (!refreshEnCurso) {
        refreshEnCurso = pedirTokensNuevos().finally(() => {
            refreshEnCurso = null; // el próximo 401 podrá renovar otra vez
        });
    }
    return refreshEnCurso;
};

// Espera a que termine el refresh en curso, si lo hay, sin importar cómo acabe.
export const esperarRefresh = async () => {
    await refreshEnCurso?.catch(() => {});
};

// ---------------------------------------------------------------------------
// Después de cada respuesta: si llega 401, renovar y reintentar
// ---------------------------------------------------------------------------
// Marca propia para no reintentar la misma petición más de una vez.
interface PeticionReintentable extends InternalAxiosRequestConfig {
    reintentada?: boolean;
}

api.interceptors.response.use(
    // Las respuestas correctas pasan sin cambios.
    (respuesta) => respuesta,
    async (error: AxiosError) => {
        const peticion = error.config as PeticionReintentable | undefined;

        // Estos errores se devuelven tal cual:
        // - los que no son 401;
        // - una petición que ya se reintentó (evita un ciclo infinito);
        // - las rutas /auth/: un 401 en login es contraseña incorrecta.
        if (
            error.response?.status !== 401 ||
            !peticion ||
            peticion.reintentada ||
            peticion.url?.startsWith('/auth/')
        ) {
            return Promise.reject(error);
        }
        peticion.reintentada = true;

        const guardados = await leerTokens();
        if (!guardados) {
            avisarSesionTerminada();
            return Promise.reject(error);
        }

        // Si la petición salió con un token distinto al guardado, otra ya lo
        // renovó: basta con reintentar, sin gastar otro refresh.
        const tokenVigente = `Bearer ${guardados.access_token}`;
        if (peticion.headers.Authorization === tokenVigente) {
            await refrescarSesion(); // si falla, la petición termina con ese error
        }

        // Al reintentar, el interceptor de arriba pone el token nuevo.
        return api(peticion);
    },
);

// ---------------------------------------------------------------------------
// Mensajes de error en español
// ---------------------------------------------------------------------------
const NOMBRES_DE_CAMPO: Record<string, string> = {
    correo: 'Correo',
    password: 'Contraseña',
    nombre: 'Nombre',
    sexo: 'Sexo',
    altura_cm: 'Altura',
};

// Convierte un error de validación (viene en inglés) en una frase legible.
const mensajeDeValidacion = (error: ErrorValidacion) => {
    // Las reglas propias del backend ya vienen en español, con este prefijo.
    if (error.msg.startsWith('Value error, ')) {
        return error.msg.replace('Value error, ', '');
    }

    const campo = String(error.loc[error.loc.length - 1]);
    const nombre = NOMBRES_DE_CAMPO[campo] ?? campo;

    switch (error.type) {
        case 'missing':
            return `${nombre}: falta este dato.`;
        case 'string_too_short':
            return `${nombre}: no cumple la longitud mínima.`;
        case 'string_too_long':
            return `${nombre}: supera la longitud máxima.`;
        case 'greater_than':
        case 'greater_than_equal':
        case 'less_than':
        case 'less_than_equal':
            return `${nombre}: está fuera del rango permitido.`;
        default:
            return `${nombre}: el valor no es válido.`;
    }
};

// getErrorMessage: recibe cualquier error y devuelve un texto para el usuario.
export const getErrorMessage = (error: unknown) => {
    // No viene de una petición HTTP.
    if (!axios.isAxiosError<ApiError>(error)) {
        return 'Ocurrió un error inesperado.';
    }
    if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
        return 'El servidor tardó demasiado en responder.';
    }
    // Sin respuesta: la petición no llegó o no volvió.
    if (!error.response) {
        return 'No se pudo conectar. Revisa tu conexión a internet.';
    }
    if (error.response.status >= 500) {
        return 'El servidor tuvo un problema. Intenta más tarde.';
    }

    const detail = error.response.data?.detail;
    if (typeof detail === 'string') {
        return detail; // regla de negocio: el backend ya la explica
    }
    if (Array.isArray(detail) && detail.length > 0) {
        return detail.map(mensajeDeValidacion).join('\n'); // validación
    }
    return 'No se pudo completar la solicitud.';
};
