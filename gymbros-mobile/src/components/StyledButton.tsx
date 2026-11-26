import { Pressable, StyleSheet, Text } from 'react-native';
import { theme } from '../theme/theme';

// StyledButton: botón principal de la app.
// Props: label (texto), color (fondo, por defecto el principal),
// handleClick (acción al presionar) y disabled (lo bloquea y lo atenúa).
interface Props {
    label: string;
    color?: string;
    handleClick: () => void;
    disabled?: boolean;
}

export const StyledButton = ({
    label,
    color = theme.colors.primary,
    handleClick,
    disabled = false,
}: Props) => {
    return (
        <Pressable
            style={({ pressed }) => [
                styles.button,
                { backgroundColor: color },
                pressed && styles.pressed,
                disabled && styles.disabled,
            ]}
            onPress={handleClick}
            disabled={disabled}
            accessibilityRole="button"
        >
            <Text style={styles.label}>{label}</Text>
        </Pressable>
    );
};

const styles = StyleSheet.create({
    button: {
        alignItems: 'center',
        borderRadius: 12,
        padding: theme.spacing.md,
    },
    pressed: { opacity: 0.7 },
    disabled: { opacity: 0.5 },
    label: {
        color: theme.colors.onPrimary,
        fontSize: theme.fontSize.md,
        fontWeight: 'bold',
    },
});
