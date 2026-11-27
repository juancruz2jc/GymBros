import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { StyleSheet, Text, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { StyledButton } from '../../components/StyledButton';
import { MainStackParamList } from '../../navigation/types';
import { theme } from '../../theme/theme';

type NavigationProp = NativeStackNavigationProp<MainStackParamList>;

export const Rutinas = () => {
    const navigation = useNavigation<NavigationProp>();

    return (
        <Screen>
            <View style={styles.container}>
                <Text style={styles.title}>Mis Rutinas</Text>
                <StyledButton
                    label="Ver catálogo de ejercicios"
                    handleClick={() => navigation.navigate('CatalogoEjercicios')}
                />
            </View>
        </Screen>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        gap: theme.spacing.md,
    },
    title: {
        color: theme.colors.text,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
    },
});