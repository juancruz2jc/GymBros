// Categoría OMS del IMC que calcula la API (RN-13).
export type CategoriaImc = 'bajo_peso' | 'normal' | 'sobrepeso' | 'obesidad';

// Una medición como la devuelve GET /mediciones. `null` = no se registró.
// `imc` y `categoria_imc` son `null` si el usuario no tiene altura en su perfil.
export interface Medicion {
    id: string;
    fecha: string; // "YYYY-MM-DD"
    peso_kg: number;
    imc: number | null;
    categoria_imc: CategoriaImc | null;
    porcentaje_grasa: number | null;
    masa_muscular_kg: number | null;
    circunf_cintura_cm: number | null;
    circunf_cadera_cm: number | null;
    circunf_brazo_cm: number | null;
    circunf_pierna_cm: number | null;
    circunf_pecho_cm: number | null;
    creado_en: string;
}
