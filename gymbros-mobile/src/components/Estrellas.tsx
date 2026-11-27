import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, View } from 'react-native';
import { theme } from '../theme/theme';

// Estrellas: calificación de 1 a 5 que se puede tocar. Para solo mostrar una
// calificación se usa Stars.
// Props: value (estrellas pintadas, 0 = sin calificar), onChange (recibe la
// estrella tocada, siempre entre 1 y 5), size y disabled.
interface Props {
    value: number;
    onChange: (value: number) => void;
    size?: number;
    disabled?: boolean;
}

const MINIMO = 1;
const MAXIMO = 5;
const ESTRELLAS = [1, 2, 3, 4, 5];

export const Estrellas = ({ value, onChange, size = 40, disabled = false }: Props) => {
    // Límites: nunca menos de 1 ni más de 5.
    const elegir = (numero: number) => onChange(Math.min(MAXIMO, Math.max(MINIMO, numero)));

    return (
        <View style={styles.row} accessibilityRole="adjustable" accessibilityLabel="Calificación">
            {ESTRELLAS.map((numero) => (
                <Pressable
                    key={numero}
                    onPress={() => elegir(numero)}
                    disabled={disabled}
                    hitSlop={6}
                    style={({ pressed }) => [pressed && styles.pressed, disabled && styles.disabled]}
                    accessibilityRole="button"
                    accessibilityLabel={`${numero} de 5 estrellas`}
                    accessibilityState={{ selected: numero <= value }}
                >
                    <Ionicons
                        name={numero <= value ? 'star' : 'star-outline'}
                        size={size}
                        color={numero <= value ? theme.colors.primary : theme.colors.border}
                    />
                </Pressable>
            ))}
        </View>
    );
};

const styles = StyleSheet.create({
    row: { flexDirection: 'row', justifyContent: 'center', gap: theme.spacing.sm },
    pressed: { opacity: 0.6 },
    disabled: { opacity: 0.5 },
});
