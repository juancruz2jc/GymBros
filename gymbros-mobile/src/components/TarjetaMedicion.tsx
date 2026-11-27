import { StyleSheet, Text, View } from 'react-native';
import { theme } from '../theme/theme';
import { CategoriaImc, Medicion } from '../types/medicion';
import { formatearFecha } from '../utils/formato';

// Texto y color de cada categoría de IMC.
const CATEGORIAS: Record<CategoriaImc, { texto: string; color: string }> = {
    bajo_peso: { texto: 'Bajo peso', color: theme.colors.primary },
    normal: { texto: 'Normal', color: theme.colors.success },
    sobrepeso: { texto: 'Sobrepeso', color: theme.colors.primary },
    obesidad: { texto: 'Obesidad', color: theme.colors.error },
};

// Texto y color de la categoría que manda la API, o null si no hay IMC.
export const obtenerCategoria = (categoria: string | null) =>
    categoria !== null && categoria in CATEGORIAS ? CATEGORIAS[categoria as CategoriaImc] : null;

// TarjetaMedicion: tarjeta con peso, IMC y categoría de una medición. Es la de
// "Tu estado actual" en Progreso y se reutiliza al comparar.
// Props: medicion y title (encabezado, por defecto "Tu estado actual").
interface Props {
    medicion: Medicion;
    title?: string;
}

export const TarjetaMedicion = ({ medicion, title = 'Tu estado actual' }: Props) => {
    const categoria = obtenerCategoria(medicion.categoria_imc);

    return (
        <View style={styles.tarjeta}>
            <Text style={styles.titulo}>{title}</Text>
            {/* Text anidado: la etiqueta normal y el valor resaltado. */}
            <Text style={styles.linea}>
                Peso: <Text style={styles.valor}>{medicion.peso_kg} kg</Text>
            </Text>
            {medicion.imc !== null ? (
                <Text style={styles.linea}>
                    IMC: <Text style={styles.valor}>{medicion.imc}</Text>
                    {categoria && (
                        <Text style={[styles.valor, { color: categoria.color }]}>
                            {' '}· {categoria.texto}
                        </Text>
                    )}
                </Text>
            ) : (
                <Text style={styles.aviso}>Agrega tu altura en Perfil para calcular tu IMC</Text>
            )}
            <Text style={styles.fecha}>{formatearFecha(medicion.fecha)}</Text>
        </View>
    );
};

const styles = StyleSheet.create({
    tarjeta: {
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 12,
        borderWidth: 1,
        gap: theme.spacing.xs,
        marginBottom: theme.spacing.md,
        padding: theme.spacing.md,
    },
    titulo: { color: theme.colors.text, fontSize: theme.fontSize.lg, fontWeight: 'bold' },
    linea: { color: theme.colors.text, fontSize: theme.fontSize.md },
    valor: { color: theme.colors.primary, fontWeight: 'bold' },
    aviso: { color: theme.colors.error, fontSize: theme.fontSize.md },
    fecha: { color: theme.colors.textMuted, fontSize: theme.fontSize.sm },
});
