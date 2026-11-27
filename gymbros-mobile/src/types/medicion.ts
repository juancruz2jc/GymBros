// Medición corporal: respuesta de /mediciones.
export interface Medicion {
    id: string;
    usuario_id: string | null;
    fecha: string; // "AAAA-MM-DD"
    peso_kg: number;
    porcentaje_grasa: number | null;
    masa_muscular_kg: number | null;
    circunf_cintura_cm: number | null;
    circunf_cadera_cm: number | null;
    circunf_brazo_cm: number | null;
    circunf_pierna_cm: number | null;
    circunf_pecho_cm: number | null;
    imc: number | null; // null si el perfil no tiene altura
    categoria_imc: string | null;
    creado_en: string;
}

// Valores posibles de `categoria_imc` (clasificación OMS, RN-13).
export type CategoriaImc = 'bajo_peso' | 'normal' | 'sobrepeso' | 'obesidad';
