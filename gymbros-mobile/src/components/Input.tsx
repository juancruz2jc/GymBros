import { StyleSheet, Text, TextInput, TextInputProps, View } from 'react-native';
import { theme } from '../theme/theme';

// Input: campo de texto con etiqueta y mensaje de error.
// Props: label, value, onChangeText, error (texto que se muestra debajo),
// secureTextEntry (oculta lo escrito, para contraseñas), keyboardType (tipo de
// teclado), autoCapitalize (mayúsculas automáticas) y autoComplete (qué dato
// puede sugerir el celular).
interface Props {
    label: string;
    value: string;
    onChangeText: (text: string) => void;
    error?: string;
    secureTextEntry?: boolean;
    keyboardType?: TextInputProps['keyboardType'];
    autoCapitalize?: TextInputProps['autoCapitalize'];
    autoComplete?: TextInputProps['autoComplete'];
}

export const Input = ({
    label,
    value,
    onChangeText,
    error = '',
    secureTextEntry = false,
    keyboardType = 'default',
    autoCapitalize = 'sentences',
    autoComplete = 'off',
}: Props) => {
    return (
        <View style={styles.container}>
            <Text style={styles.label}>{label}</Text>
            <TextInput
                style={[styles.input, error !== '' && styles.inputError]}
                value={value}
                onChangeText={onChangeText}
                secureTextEntry={secureTextEntry}
                keyboardType={keyboardType}
                autoCapitalize={autoCapitalize}
                autoComplete={autoComplete}
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
