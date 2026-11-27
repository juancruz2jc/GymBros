import { Ionicons } from '@expo/vector-icons';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { theme } from '../theme/theme';
import { Ejercicio } from '../types/ejercicio';

export interface EjercicioItemProps {
    ejercicio: Ejercicio;
    onPress?: (ejercicio: Ejercicio) => void;
    onSelect?: (ejercicio: Ejercicio) => void;
}

export const EjercicioItem = ({ ejercicio, onPress, onSelect }: EjercicioItemProps) => {
    const handlePress = () => {
        if (onSelect) {
            onSelect(ejercicio);
        } else if (onPress) {
            onPress(ejercicio);
        }
    };

    return (
        <Pressable
            onPress={handlePress}
            style={({ pressed }) => [styles.card, pressed && styles.pressed]}
            accessibilityRole="button"
            accessibilityLabel={ejercicio.nombre_es}
        >
            <View style={styles.thumbWrapper}>
                {ejercicio.gif_url ? (
                    <>
                        <Image
                            source={{ uri: ejercicio.gif_url }}
                            style={styles.thumbnail}
                            resizeMode="cover"
                        />
                        <View style={styles.gifPill}>
                            <Text style={styles.gifPillText}>Gif</Text>
                        </View>
                    </>
                ) : (
                    <View style={styles.placeholder}>
                        <Ionicons name="image-outline" size={22} color={theme.colors.primary} />
                    </View>
                )}
            </View>

            <View style={styles.info}>
                <Text style={styles.nombre} numberOfLines={1}>
                    {ejercicio.nombre_es}
                </Text>
                <Text style={styles.meta} numberOfLines={1}>
                    <Text style={styles.grupo}>{ejercicio.grupo_muscular}</Text>
                    {'  •  '}
                    <Text style={styles.equipo}>{ejercicio.equipo}</Text>
                </Text>
            </View>

            <Ionicons
                name={onSelect ? 'add-circle-outline' : 'chevron-forward'}
                size={onSelect ? 24 : 18}
                color={onSelect ? theme.colors.primary : theme.colors.textMuted}
            />
        </Pressable>
    );
};

const styles = StyleSheet.create({
    card: {
        alignItems: 'center',
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 16,
        borderWidth: 1,
        flexDirection: 'row',
        gap: theme.spacing.md,
        marginBottom: theme.spacing.sm,
        padding: theme.spacing.sm,
    },
    pressed: {
        opacity: 0.75,
    },
    thumbWrapper: {
        height: 56,
        position: 'relative',
        width: 56,
    },
    thumbnail: {
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 12,
        height: 56,
        width: 56,
    },
    gifPill: {
        backgroundColor: '#1E1B18',
        borderRadius: 6,
        bottom: 4,
        paddingHorizontal: 5,
        paddingVertical: 1,
        position: 'absolute',
        right: 4,
    },
    gifPillText: {
        color: '#FFFFFF',
        fontSize: 9,
        fontWeight: 'bold',
    },
    placeholder: {
        alignItems: 'center',
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 12,
        height: 56,
        justifyContent: 'center',
        width: 56,
    },
    info: {
        flex: 1,
        gap: 4,
    },
    nombre: {
        color: theme.colors.text,
        fontSize: theme.fontSize.md,
        fontWeight: 'bold',
    },
    meta: {
        fontSize: theme.fontSize.sm,
    },
    grupo: {
        color: theme.colors.primary,
        fontWeight: '600',
        textTransform: 'capitalize',
    },
    equipo: {
        color: theme.colors.textMuted,
        textTransform: 'capitalize',
    },
});