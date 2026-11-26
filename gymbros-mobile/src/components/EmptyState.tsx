import { StyleSheet, Text, View } from 'react-native';
import { theme } from '../theme/theme';
import { StyledButton } from './StyledButton';

// EmptyState: se muestra cuando una lista o pantalla no tiene datos.
// Props: message (explicación), y de forma opcional actionLabel y onAction para
// mostrar un botón. El botón solo aparece si se envían las dos.
interface Props {
    message: string;
    actionLabel?: string;
    onAction?: () => void;
}

export const EmptyState = ({ message, actionLabel = '', onAction }: Props) => {
    return (
        <View style={styles.container}>
            <Text style={styles.message}>{message}</Text>
            {actionLabel !== '' && onAction && (
                <StyledButton label={actionLabel} handleClick={onAction} />
            )}
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        gap: theme.spacing.md,
    },
    message: {
        color: theme.colors.textMuted,
        fontSize: theme.fontSize.md,
        textAlign: 'center',
    },
});
