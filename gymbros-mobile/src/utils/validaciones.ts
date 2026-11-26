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
