import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import { Tokens } from '../types/auth';

// Guarda los tokens en el dispositivo para no pedir login cada vez.
// En el celular usa SecureStore, que los cifra (Keychain en iOS, Keystore en
// Android).
// En web SecureStore no existe: se usa localStorage SOLO como alternativa de
// desarrollo, porque no cifra nada.

const CLAVE_ACCESS = 'gymbros.access_token';
const CLAVE_REFRESH = 'gymbros.refresh_token';

// De la respuesta de la API solo se guardan los dos tokens.
export type TokensGuardados = Pick<Tokens, 'access_token' | 'refresh_token'>;

const guardarValor = async (clave: string, valor: string) => {
    if (Platform.OS === 'web') {
        localStorage.setItem(clave, valor);
        return;
    }
    await SecureStore.setItemAsync(clave, valor);
};

const leerValor = async (clave: string) => {
    if (Platform.OS === 'web') {
        return localStorage.getItem(clave);
    }
    return SecureStore.getItemAsync(clave);
};

const borrarValor = async (clave: string) => {
    if (Platform.OS === 'web') {
        localStorage.removeItem(clave);
        return;
    }
    await SecureStore.deleteItemAsync(clave);
};

export const guardarTokens = async (tokens: TokensGuardados) => {
    // Primero el refresh: es el que permite recuperar la sesión.
    await guardarValor(CLAVE_REFRESH, tokens.refresh_token);
    await guardarValor(CLAVE_ACCESS, tokens.access_token);
};

// Devuelve null si no hay una sesión guardada.
export const leerTokens = async (): Promise<TokensGuardados | null> => {
    const access_token = await leerValor(CLAVE_ACCESS);
    const refresh_token = await leerValor(CLAVE_REFRESH);
    if (!access_token || !refresh_token) {
        return null;
    }
    return { access_token, refresh_token };
};

export const borrarTokens = async () => {
    await borrarValor(CLAVE_REFRESH);
    await borrarValor(CLAVE_ACCESS);
};
