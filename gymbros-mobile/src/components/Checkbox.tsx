import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text } from 'react-native';
import { theme } from '../theme/theme';

// Checkbox: casilla para marcar o desmarcar, con su texto.
// Props: label (texto), checked (si está marcada), handleChange (recibe el valor
// nuevo al tocarla) y disabled (la bloquea).
interface Props {
    label: string;
    checked: boolean;
    handleChange: (checked: boolean) => void;
    disabled?: boolean;
}

export const Checkbox = ({ label, checked, handleChange, disabled = false }: Props) => {
    return (
        <Pressable
            style={({ pressed }) => [
                styles.row,
                pressed && styles.pressed,
                disabled && styles.disabled,
            ]}
            onPress={() => handleChange(!checked)}
            disabled={disabled}
            accessibilityRole="checkbox"
            accessibilityState={{ checked, disabled }}
        >
            <Ionicons
                name={checked ? 'checkbox' : 'square-outline'}
                size={24}
                color={theme.colors.primary}
            />
            <Text style={styles.label}>{label}</Text>
        </Pressable>
    );
};

const styles = StyleSheet.create({
    row: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: theme.spacing.sm,
        marginBottom: theme.spacing.md,
    },
    pressed: { opacity: 0.7 },
    disabled: { opacity: 0.5 },
    label: {
        flex: 1, // el texto largo baja a la línea siguiente
        color: theme.colors.text,
        fontSize: theme.fontSize.sm,
    },
});
