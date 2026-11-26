import { Pressable, StyleSheet, Text, View } from 'react-native';
import { theme } from '../theme/theme';

export interface ChipOption {
    value: string; // lo que se guarda
    label: string; // lo que se ve
}

// Chips: opciones en forma de píldora, para elegir una.
// Props: label (título), options, selected (valor marcado, o null), handleChange
// (recibe el valor tocado) y disabled (bloquea todas).
interface Props {
    label: string;
    options: ChipOption[];
    selected?: string | null;
    handleChange: (value: string) => void;
    disabled?: boolean;
}

export const Chips = ({ label, options, selected = null, handleChange, disabled = false }: Props) => {
    return (
        <View style={styles.container}>
            <Text style={styles.label}>{label}</Text>
            <View style={styles.row}>
                {options.map((option) => {
                    const checked = option.value === selected;
                    return (
                        <Pressable
                            key={option.value}
                            style={({ pressed }) => [
                                styles.chip,
                                checked && styles.chipChecked,
                                pressed && styles.pressed,
                                disabled && styles.disabled,
                            ]}
                            onPress={() => handleChange(option.value)}
                            disabled={disabled}
                            accessibilityRole="radio"
                            accessibilityState={{ checked, disabled }}
                        >
                            <Text style={[styles.text, checked && styles.textChecked]}>
                                {option.label}
                            </Text>
                        </Pressable>
                    );
                })}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { marginBottom: theme.spacing.md },
    label: {
        color: theme.colors.text,
        fontSize: theme.fontSize.sm,
        marginBottom: theme.spacing.xs,
    },
    // flexWrap: si no caben en una fila, bajan a la siguiente.
    row: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.spacing.sm },
    chip: {
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 24,
        borderWidth: 1,
        paddingHorizontal: theme.spacing.md,
        paddingVertical: theme.spacing.sm,
    },
    chipChecked: {
        backgroundColor: theme.colors.primarySoft,
        borderColor: theme.colors.primaryText,
    },
    pressed: { opacity: 0.7 },
    disabled: { opacity: 0.5 },
    text: { color: theme.colors.text, fontSize: theme.fontSize.sm },
    textChecked: { color: theme.colors.primaryText, fontWeight: 'bold' },
});
