export interface Ejercicio {
    id: string;
    nombre_es: string;
    grupo_muscular: string;
    equipo: string;
    categoria: string;
    gif_url: string | null;
}

export interface FiltrosEjercicio {
    grupo_muscular?: string;
    equipo?: string;
    categoria?: string;
}