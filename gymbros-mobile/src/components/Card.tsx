import { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { theme } from '../theme/theme';

// Card: tarjeta con un título pequeño para agrupar información.
// Props: title (encabezado) y children (contenido).
interface Props {
    title: string;
    children: ReactNode;
}

export const Card = ({ title, children }: Props) => {
    return (
        <View style={styles.card}>
            <Text style={styles.title}>{title}</Text>
            {children}
        </View>
    );
};

const styles = StyleSheet.create({
    card: {
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 16,
        borderWidth: 1,
        gap: theme.spacing.xs,
        marginBottom: theme.spacing.md,
        padding: theme.spacing.md,
    },
    title: {
        color: theme.colors.textMuted,
        fontSize: theme.fontSize.sm,
        fontWeight: 'bold',
    },
});
