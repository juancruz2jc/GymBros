import { ReactNode } from 'react';
import { StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { theme } from '../theme/theme';

// Screen: contenedor base de todas las pantallas. Pone el fondo y el padding
// comunes y evita el notch y las barras del sistema.
// Props: children (contenido de la pantalla).
interface Props {
    children: ReactNode;
}

export const Screen = ({ children }: Props) => {
    return <SafeAreaView style={styles.screen}>{children}</SafeAreaView>;
};

const styles = StyleSheet.create({
    screen: {
        flex: 1,
        backgroundColor: theme.colors.background,
        padding: theme.spacing.md,
    },
});
