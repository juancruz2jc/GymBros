import { Pressable, StyleSheet, Text } from 'react-native';
import { theme } from '../theme/theme';

// TextLink: texto que se puede tocar, para pasar de una pantalla a otra.
// Props: label (texto), handleClick (acción) y disabled (lo bloquea).
interface Props {
    label: string;
    handleClick: () => void;
    disabled?: boolean;
}

export const TextLink = ({ label, handleClick, disabled = false }: Props) => {
    return (
        <Pressable
            style={({ pressed }) => [
                styles.link,
                pressed && styles.pressed,
                disabled && styles.disabled,
            ]}
            onPress={handleClick}
            disabled={disabled}
            accessibilityRole="link"
        >
            <Text style={styles.label}>{label}</Text>
        </Pressable>
    );
};

const styles = StyleSheet.create({
    link: {
        alignItems: 'center',
        padding: theme.spacing.md,
    },
    pressed: { opacity: 0.7 },
    disabled: { opacity: 0.5 },
    label: {
        color: theme.colors.primaryText, // más oscuro: se lee mejor en texto pequeño
        fontSize: theme.fontSize.md,
        fontWeight: 'bold',
    },
});
