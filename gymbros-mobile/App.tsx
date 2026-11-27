import { DefaultTheme, NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from './src/context/AuthContext';
import { RootNavigator } from './src/navigation/RootNavigator';
import { theme } from './src/theme/theme';

// Colores que usan los encabezados y fondos de React Navigation.
const temaNavegacion = {
    ...DefaultTheme,
    colors: {
        ...DefaultTheme.colors,
        primary: theme.colors.primary,
        background: theme.colors.background,
        card: theme.colors.background,
        text: theme.colors.text,
        border: theme.colors.border,
    },
};

// App: componente raíz. Prepara el área segura, la sesión y la navegación.
export const App = () => {
    return (
        <SafeAreaProvider>
            <AuthProvider>
                <NavigationContainer theme={temaNavegacion}>
                    <RootNavigator />
                    <StatusBar style="auto" />
                </NavigationContainer>
            </AuthProvider>
        </SafeAreaProvider>
    );
};
