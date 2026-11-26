import { NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from './src/context/AuthContext';
import { RootNavigator } from './src/navigation/RootNavigator';

// App: componente raíz. Prepara el área segura, la sesión y la navegación.
export const App = () => {
    return (
        <SafeAreaProvider>
            <AuthProvider>
                <NavigationContainer>
                    <RootNavigator />
                    <StatusBar style="auto" />
                </NavigationContainer>
            </AuthProvider>
        </SafeAreaProvider>
    );
};
