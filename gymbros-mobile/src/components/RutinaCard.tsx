import { Ionicons } from '@expo/vector-icons';
import { Alert, Pressable, StyleSheet, Text, View } from 'react-native';
import { theme } from '../theme/theme';
import { Rutina } from '../types/rutina';

export interface RutinaCardProps {
    rutina: Rutina;
    onPress: (rutina: Rutina) => void;
    onToggleFavorita: (id: string) => void;
    onEditar: (rutina: Rutina) => void;
    onDuplicar: (rutina: Rutina) => void;
    onEliminar: (rutina: Rutina) => void;
}

const formatearFechaRelativa = (fechaIso: string | null): string => {
    if (!fechaIso) return 'Actualizada hoy';
    const fecha = new Date(fechaIso);
    const ahora = new Date();
    const diffMs = ahora.getTime() - fecha.getTime();
    const diffDias = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDias <= 0) return 'Actualizada hoy';
    if (diffDias === 1) return 'Actualizada ayer';
    if (diffDias < 7) return `Actualizada hace ${diffDias} días`;
    const semanas = Math.floor(diffDias / 7);
    return semanas === 1 ? 'Actualizada hace 1 semana' : `Actualizada hace ${semanas} semanas`;
};

export const RutinaCard = ({
    rutina,
    onPress,
    onToggleFavorita,
    onEditar,
    onDuplicar,
    onEliminar,
}: RutinaCardProps) => {
    const cantidadEjercicios = rutina.ejercicios?.length ?? 0;

    const handleLongPress = () => {
        Alert.alert(rutina.nombre, 'Selecciona una acción para esta rutina', [
            { text: 'Duplicar', onPress: () => onDuplicar(rutina) },
            { text: 'Eliminar', style: 'destructive', onPress: () => onEliminar(rutina) },
            { text: 'Cancelar', style: 'cancel' },
        ]);
    };

    return (
        <Pressable
            onPress={() => onPress(rutina)}
            onLongPress={handleLongPress}
            style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
            accessibilityRole="button"
            accessibilityLabel={`Rutina ${rutina.nombre}`}
        >
            <View style={styles.topRow}>
                <Text style={styles.nombre} numberOfLines={2}>
                    {rutina.nombre}
                </Text>

                <Pressable
                    onPress={() => onToggleFavorita(rutina.id)}
                    hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
                    style={styles.starButton}
                    accessibilityRole="button"
                    accessibilityLabel={
                        rutina.favorita ? 'Quitar de favoritas' : 'Marcar como favorita'
                    }
                >
                    <Ionicons
                        name={rutina.favorita ? 'star' : 'star-outline'}
                        size={20}
                        color={rutina.favorita ? theme.colors.primary : theme.colors.textMuted}
                    />
                </Pressable>
            </View>

            <Text style={styles.meta}>
                {cantidadEjercicios} {cantidadEjercicios === 1 ? 'ejercicio' : 'ejercicios'}
                {'  •  '}
                {formatearFechaRelativa(rutina.actualizado_en ?? rutina.creado_en)}
            </Text>

            <View style={styles.actionsRow}>
                <Pressable
                    style={({ pressed }) => [styles.actionPill, pressed && styles.pillPressed]}
                    onPress={() => onEditar(rutina)}
                >
                    <Ionicons name="pencil-outline" size={13} color={theme.colors.text} />
                    <Text style={styles.actionPillText}>Editar</Text>
                </Pressable>

                <Pressable
                    style={({ pressed }) => [styles.actionPill, pressed && styles.pillPressed]}
                    onPress={() => onDuplicar(rutina)}
                >
                    <Ionicons name="copy-outline" size={13} color={theme.colors.text} />
                    <Text style={styles.actionPillText}>Duplicar</Text>
                </Pressable>

                <Pressable
                    style={({ pressed }) => [styles.actionPill, pressed && styles.pillPressed]}
                    onPress={() => onEliminar(rutina)}
                >
                    <Ionicons name="trash-outline" size={13} color={theme.colors.text} />
                    <Text style={styles.actionPillText}>Eliminar</Text>
                </Pressable>
            </View>
        </Pressable>
    );
};

const styles = StyleSheet.create({
    card: {
        backgroundColor: theme.colors.primarySoft,
        borderColor: theme.colors.border,
        borderRadius: 16,
        borderWidth: 1,
        gap: theme.spacing.sm,
        marginBottom: theme.spacing.md,
        padding: theme.spacing.md,
    },
    cardPressed: {
        opacity: 0.8,
        transform: [{ scale: 0.99 }],
    },
    topRow: {
        alignItems: 'flex-start',
        flexDirection: 'row',
        gap: theme.spacing.sm,
        justifyContent: 'space-between',
    },
    nombre: {
        color: theme.colors.text,
        flex: 1,
        fontSize: theme.fontSize.md,
        fontWeight: 'bold',
    },
    starButton: {
        padding: 2,
    },
    meta: {
        color: theme.colors.textMuted,
        fontSize: theme.fontSize.sm,
    },
    actionsRow: {
        flexDirection: 'row',
        gap: theme.spacing.sm,
        marginTop: 4,
    },
    actionPill: {
        alignItems: 'center',
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 16,
        borderWidth: 1,
        flexDirection: 'row',
        gap: 4,
        paddingHorizontal: 10,
        paddingVertical: 5,
    },
    pillPressed: {
        opacity: 0.7,
    },
    actionPillText: {
        color: theme.colors.text,
        fontSize: 12,
        fontWeight: '600',
    },
});