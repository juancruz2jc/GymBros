import { StyleSheet, Text, TextInput, View } from 'react-native';
import { theme } from '../theme/theme';

// Input: campo de texto con etiqueta y mensaje de error.
// Props: label, value, onChangeText, error (texto que se muestra debajo) y
// secureTextEntry (oculta lo escrito, para contraseñas).
interface Props {
    label: string;
    value: string;
    onChangeText: (text: string) => void;
    error?: string;
    secureTextEntry?: boolean;
}

export const Input = ({
    label,
    value,
    onChangeText,
    error = '',
    secureTextEntry = false,
}: Props) => {
    return (
        <View style={styles.container}>
            <Text style={styles.label}>{label}</Text>
            <TextInput
                style={[styles.input, error !== '' && styles.inputError]}
                value={value}
                onChangeText={onChangeText}
                secureTextEntry={secureTextEntry}
                accessibilityLabel={label}
            />
            {error !== '' && <Text style={styles.error}>{error}</Text>}
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
    input: {
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 12,
        borderWidth: 1,
        color: theme.colors.text,
        fontSize: theme.fontSize.md,
        padding: theme.spacing.md,
    },
    inputError: { borderColor: theme.colors.error },
    error: {
        color: theme.colors.error,
        fontSize: theme.fontSize.sm,
        marginTop: theme.spacing.xs,
    },
});
