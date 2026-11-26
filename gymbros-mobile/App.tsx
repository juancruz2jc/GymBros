import { NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { RootNavigator } from './src/navigation/RootNavigator';

// App: componente raíz. Prepara el área segura y la navegación.
export const App = () => {
    return (
        <SafeAreaProvider>
            <NavigationContainer>
                <RootNavigator />
                <StatusBar style="auto" />
            </NavigationContainer>
        </SafeAreaProvider>
    );
};
