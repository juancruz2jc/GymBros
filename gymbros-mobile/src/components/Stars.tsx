import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, View } from 'react-native';
import { theme } from '../theme/theme';

// Stars: muestra una calificación de 1 a 5 con estrellas (solo lectura).
// Props: value (cuántas van pintadas) y size (tamaño de cada una).
interface Props {
    value: number;
    size?: number;
}

const ESTRELLAS = [1, 2, 3, 4, 5];

export const Stars = ({ value, size = 18 }: Props) => {
    return (
        <View style={styles.row} accessible accessibilityLabel={`Calificación: ${value} de 5`}>
            {ESTRELLAS.map((numero) => (
                <Ionicons
                    key={numero}
                    name="star"
                    size={size}
                    color={numero <= value ? theme.colors.primary : theme.colors.border}
                />
            ))}
        </View>
    );
};

const styles = StyleSheet.create({
    row: { flexDirection: 'row' },
});
