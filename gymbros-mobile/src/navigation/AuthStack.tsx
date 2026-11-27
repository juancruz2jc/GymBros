import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Login } from '../screens/auth/Login';
import { Registro } from '../screens/auth/Registro';
import { AuthStackParamList } from './types';

const Stack = createNativeStackNavigator<AuthStackParamList>();

// AuthStack: pantallas que se ven sin sesión iniciada.
export const AuthStack = () => {
    return (
        <Stack.Navigator>
            <Stack.Screen name="Login" component={Login} />
            <Stack.Screen name="Registro" component={Registro} />
        </Stack.Navigator>
    );
};
