// Validaciones de formularios. Cada función devuelve el mensaje de error, o ''
// cuando el valor es válido (así se pasa directo a la prop `error` de Input).
// Sirven para avisar antes de enviar; la API vuelve a validar todo.

// Algo antes de la @, algo después, un punto y una terminación, sin espacios.
const FORMATO_CORREO = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const validarCorreo = (correo: string) => {
    const limpio = correo.trim();
    if (limpio === '') {
        return 'Escribe tu correo.';
    }
    if (!FORMATO_CORREO.test(limpio)) {
        return 'El correo no tiene un formato válido.';
    }
    return '';
};

// Para campos que solo deben venir llenos, como la contraseña del login.
export const validarRequerido = (valor: string, mensaje: string) => {
    return valor === '' ? mensaje : '';
};

// El backend acepta nombres de 1 a 100 caracteres.
export const validarNombre = (nombre: string) => {
    const limpio = nombre.trim();
    if (limpio === '') {
        return 'Escribe tu nombre.';
    }
    if (limpio.length > 100) {
        return 'El nombre admite máximo 100 caracteres.';
    }
    return '';
};

// Mismas reglas que el backend (RN-21): de 8 a 128 caracteres, con al menos una
// letra y un número.
export const validarPasswordNueva = (password: string) => {
    if (password.length < 8 || password.length > 128) {
        return 'La contraseña debe tener entre 8 y 128 caracteres.';
    }
    if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
        return 'La contraseña debe incluir al menos una letra y un número.';
    }
    return '';
};

export const validarConfirmacion = (password: string, confirmacion: string) => {
    if (confirmacion === '') {
        return 'Confirma tu contraseña.';
    }
    return password === confirmacion ? '' : 'Las contraseñas no coinciden.';
};

// Al editar el perfil, la API exige un nombre de 2 a 100 caracteres.
export const validarNombrePerfil = (nombre: string) => {
    const limpio = nombre.trim();
    if (limpio.length < 2 || limpio.length > 100) {
        return 'El nombre debe tener entre 2 y 100 caracteres.';
    }
    return '';
};

// La altura es opcional; si se escribe, debe ser un entero de 51 a 299.
export const validarAltura = (altura: string) => {
    const limpia = altura.trim();
    if (limpia === '') {
        return '';
    }
    if (!/^\d+$/.test(limpia)) {
        return 'Escribe la altura en centímetros, sin decimales.';
    }
    const valor = Number(limpia);
    if (valor < 51 || valor > 299) {
        return 'La altura debe estar entre 51 y 299 cm.';
    }
    return '';
};
