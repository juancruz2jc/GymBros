import { Pressable, StyleSheet, Text } from 'react-native';
import { theme } from '../theme/theme';

// FAB: botón flotante fijo en una esquina inferior de la pantalla.
// Props: label (texto), position ("left" o "right"), color (fondo, por defecto
// el principal), onPress y onLongPress.
interface Props {
    label: string;
    position?: "left" | "right";
    color?: string;
    onPress?: () => void;
    onLongPress?: () => void;
}

export const FAB = ({
    label,
    position = "right",
    color = theme.colors.primary,
    onPress,
    onLongPress,
}: Props) => {
    return (
        <Pressable
            // Pressable llama a la función de style con un objeto: { pressed: boolean }.
            // Hay que escribir ({ pressed }) para sacar el booleano. Con (pressed) la
            // variable sería el objeto completo, y un objeto siempre es truthy: el
            // botón se vería presionado todo el tiempo.
            style={({ pressed }) => [
                styles.floattingButton,
                position === "right" ? styles.positionRight : styles.positionLeft,
                { backgroundColor: color },
                pressed ? { opacity: 0.7 } : { opacity: 1 },
            ]}
            onPress={onPress}
            onLongPress={onLongPress}
        >
            <Text style={{ color: "white", fontSize: 20 }}>{label}</Text>
        </Pressable>
    );
};

const styles = StyleSheet.create({
    floattingButton: {
        position: "absolute", bottom: 20,
        borderRadius: 15, padding: 10, shadowColor: "#000",
        shadowOffset: { width: 0, height: 4 }, elevation: 3,
    },
    positionRight: { right: 20 },
    positionLeft: { left: 20 },
});
