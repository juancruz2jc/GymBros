import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { theme } from '../theme/theme';

// Loading: indicador centrado mientras se cargan datos.
// Props: color (por defecto el principal).
interface Props {
    color?: string;
}

export const Loading = ({ color = theme.colors.primary }: Props) => {
    return (
        <View style={styles.container}>
            <ActivityIndicator size="large" color={color} />
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
    },
});
