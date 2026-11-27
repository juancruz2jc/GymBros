// Par de tokens que devuelven login, registro y refresh.
export interface Tokens {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number; // segundos de vida del access_token
}

// Cuerpo de POST /auth/login.
export interface LoginDatos {
    correo: string;
    password: string;
}

// Cuerpo de POST /auth/registro. La API exige consentimiento_datos en true.
export interface RegistroDatos {
    correo: string;
    password: string;
    nombre: string;
    consentimiento_datos: boolean;
}
