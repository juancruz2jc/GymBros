import { ReactNode } from 'react';
import { KeyboardAvoidingView, ScrollView, StyleSheet } from 'react-native';

// FormScroll: contenedor de formularios. Deja desplazar la pantalla para que el
// teclado no tape los campos.
// Props: children (los campos y botones).
interface Props {
    children: ReactNode;
}

export const FormScroll = ({ children }: Props) => {
    return (
        <KeyboardAvoidingView style={styles.container} behavior="padding">
            {/* "handled": el primer toque en un botón funciona con el teclado abierto. */}
            <ScrollView keyboardShouldPersistTaps="handled">{children}</ScrollView>
        </KeyboardAvoidingView>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1 },
});
