import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { theme } from '../theme/theme';
import { SesionHistorialItem } from '../types/sesion';
import { formatearDuracion, formatearFechaHoraColombia } from '../utils/formato';
import { Stars } from './Stars';

// TarjetaSesion: un entrenamiento finalizado dentro del historial.
// Props: sesion (item de GET /sesiones) y onPress (opcional: sin ella la
// tarjeta no se puede tocar).
interface Props {
    sesion: SesionHistorialItem;
    onPress?: (sesion: SesionHistorialItem) => void;
}

export const TarjetaSesion = ({ sesion, onPress }: Props) => {
    return (
        <Pressable
            onPress={onPress ? () => onPress(sesion) : undefined}
            disabled={!onPress}
            style={({ pressed }) => [styles.card, pressed && styles.pressed]}
            accessibilityRole={onPress ? 'button' : undefined}
        >
            <View style={styles.icono}>
                <Ionicons name="barbell-outline" size={22} color={theme.colors.primary} />
            </View>

            <View style={styles.info}>
                {/* El backend ya manda "Entrenamiento libre" cuando no hay rutina. */}
                <Text style={styles.nombre} numberOfLines={1}>
                    {sesion.rutina_nombre}
                </Text>
                <Text style={styles.detalle}>{formatearFechaHoraColombia(sesion.iniciada_en)}</Text>
                <View style={styles.fila}>
                    <Text style={styles.detalle}>
                        {sesion.duracion_segundos !== null
                            ? formatearDuracion(sesion.duracion_segundos)
                            : '—'}
                    </Text>
                    {/* Calificar es opcional: sin calificación no hay estrellas. */}
                    {sesion.calificacion !== null ? (
                        <Stars value={sesion.calificacion} size={14} />
                    ) : (
                        <Text style={styles.sinCalificar}>Sin calificar</Text>
                    )}
                </View>
            </View>

            {onPress && (
                <Ionicons name="chevron-forward" size={18} color={theme.colors.textMuted} />
            )}
        </Pressable>
    );
};

const styles = StyleSheet.create({
    card: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: theme.spacing.md,
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 16,
        borderWidth: 1,
        marginBottom: theme.spacing.sm,
        padding: theme.spacing.md,
    },
    pressed: { opacity: 0.7 },
    icono: {
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 12,
        height: 44,
        width: 44,
    },
    info: { flex: 1, gap: 2 },
    nombre: { color: theme.colors.text, fontSize: theme.fontSize.md, fontWeight: 'bold' },
    detalle: { color: theme.colors.textMuted, fontSize: theme.fontSize.sm },
    fila: { flexDirection: 'row', alignItems: 'center', gap: theme.spacing.sm },
    sinCalificar: { color: theme.colors.textMuted, fontSize: 12, fontStyle: 'italic' },
});
