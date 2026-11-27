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

// Campos opcionales que el usuario puede registrar en una medición.
export type CampoOpcional =
    | 'porcentaje_grasa'
    | 'masa_muscular_kg'
    | 'circunf_cintura_cm'
    | 'circunf_cadera_cm'
    | 'circunf_brazo_cm'
    | 'circunf_pierna_cm'
    | 'circunf_pecho_cm';

// Cuerpo de POST /mediciones y PUT /mediciones/{id}. Los opcionales que no se
// envían quedan vacíos (o sin cambios, en el PUT).
export type MedicionDatos = {
    fecha: string; // "AAAA-MM-DD"
    peso_kg: number;
} & Partial<Record<CampoOpcional, number>>;

// Diferencias de GET /mediciones/comparar: reciente − anterior. `null` si a
// alguna de las dos le falta ese dato.
export type DiferenciasMedicion = Record<CampoOpcional | 'peso_kg' | 'imc', number | null>;

// Respuesta de GET /mediciones/comparar.
export interface MedicionComparativa {
    medicion_anterior: Medicion;
    medicion_reciente: Medicion;
    diferencias: DiferenciasMedicion;
}
