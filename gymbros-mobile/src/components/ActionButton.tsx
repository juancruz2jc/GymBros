import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { theme } from '../theme/theme';

// ActionButton: botón grande para la acción principal de una pantalla, con un
// ícono de reproducir a la derecha.
// Props: title, subtitle (texto pequeño opcional), handleClick y disabled.
interface Props {
    title: string;
    subtitle?: string;
    handleClick: () => void;
    disabled?: boolean;
}

export const ActionButton = ({ title, subtitle = '', handleClick, disabled = false }: Props) => {
    return (
        <Pressable
            style={({ pressed }) => [
                styles.button,
                pressed && styles.pressed,
                disabled && styles.disabled,
            ]}
            onPress={handleClick}
            disabled={disabled}
            accessibilityRole="button"
        >
            <View style={styles.texts}>
                <Text style={styles.title}>{title}</Text>
                {subtitle !== '' && <Text style={styles.subtitle}>{subtitle}</Text>}
            </View>
            <View style={styles.circle}>
                <Ionicons name="play-outline" size={24} color={theme.colors.onPrimary} />
            </View>
        </Pressable>
    );
};

const styles = StyleSheet.create({
    button: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: theme.colors.primary,
        borderRadius: 20,
        gap: theme.spacing.md,
        marginBottom: theme.spacing.md,
        padding: theme.spacing.lg,
    },
    pressed: { opacity: 0.7 },
    disabled: { opacity: 0.5 },
    texts: { flex: 1, gap: theme.spacing.xs },
    title: {
        color: theme.colors.onPrimary,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
    },
    subtitle: {
        color: theme.colors.onPrimary,
        fontSize: theme.fontSize.sm,
    },
    circle: {
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.25)',
        borderRadius: 22,
        height: 44,
        width: 44,
    },
});
