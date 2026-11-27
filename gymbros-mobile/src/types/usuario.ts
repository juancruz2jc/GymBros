// Perfil que devuelve GET /usuarios/me. `null` = el usuario no lo ha llenado.
export interface Usuario {
    id: string;
    correo: string;
    nombre: string;
    sexo: string | null;
    altura_cm: number | null;
    foto_url: string | null;
    codigo_gimnasio: string | null;
    tiene_experiencia_previa: boolean | null;
    preferencias_notificacion: Record<string, unknown> | null;
}

// Cuerpo de PUT /usuarios/me. Solo se envían los campos que cambian; null borra
// el dato (el nombre no se puede borrar).
export interface UsuarioActualizar {
    nombre?: string;
    sexo?: string | null;
    altura_cm?: number | null;
}
