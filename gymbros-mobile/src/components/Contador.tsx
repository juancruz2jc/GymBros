import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { theme } from '../theme/theme';

// Contador: valor con botones - y + que respetan un mínimo y un máximo.
// Props: label (qué se cuenta), value (texto que se muestra), handleMenos y
// handleMas (acciones), puedeMenos y puedeMas (bloquean el botón en el límite).
interface Props {
    label: string;
    value: string;
    handleMenos: () => void;
    handleMas: () => void;
    puedeMenos: boolean;
    puedeMas: boolean;
}

const HIT_SLOP = 12; // agranda la zona táctil de los botones pequeños

export const Contador = ({ label, value, handleMenos, handleMas, puedeMenos, puedeMas }: Props) => {
    return (
        <View style={styles.container}>
            <Text style={styles.label}>{label}</Text>
            <View style={styles.row}>
                <Pressable
                    onPress={handleMenos}
                    disabled={!puedeMenos}
                    hitSlop={HIT_SLOP}
                    style={({ pressed }) => [
                        styles.button,
                        pressed && styles.pressed,
                        !puedeMenos && styles.disabled,
                    ]}
                    accessibilityRole="button"
                    accessibilityLabel={`Restar ${label.toLowerCase()}`}
                >
                    <Ionicons name="remove" size={24} color={theme.colors.onPrimary} />
                </Pressable>
                <Text style={styles.value}>{value}</Text>
                <Pressable
                    onPress={handleMas}
                    disabled={!puedeMas}
                    hitSlop={HIT_SLOP}
                    style={({ pressed }) => [
                        styles.button,
                        pressed && styles.pressed,
                        !puedeMas && styles.disabled,
                    ]}
                    accessibilityRole="button"
                    accessibilityLabel={`Sumar ${label.toLowerCase()}`}
                >
                    <Ionicons name="add" size={24} color={theme.colors.onPrimary} />
                </Pressable>
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, alignItems: 'center', gap: theme.spacing.xs },
    label: { color: theme.colors.textMuted, fontSize: theme.fontSize.sm },
    row: { flexDirection: 'row', alignItems: 'center', gap: theme.spacing.sm },
    button: {
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: theme.colors.primary,
        borderRadius: 20,
        height: 40,
        width: 40,
    },
    pressed: { opacity: 0.7 },
    disabled: { opacity: 0.35 },
    value: {
        color: theme.colors.text,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
        minWidth: 64,
        textAlign: 'center',
    },
});
