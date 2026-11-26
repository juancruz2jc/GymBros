import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { DetalleEntrenamiento } from '../screens/historial/DetalleEntrenamiento';
import { EntrenamientoActivo } from '../screens/entrenamiento/EntrenamientoActivo';
import { Resumen } from '../screens/entrenamiento/Resumen';
import { CompararMediciones } from '../screens/progreso/CompararMediciones';
import { RegistrarMedicion } from '../screens/progreso/RegistrarMedicion';
import { CrearRutina } from '../screens/rutinas/CrearRutina';
import { DetalleRutina } from '../screens/rutinas/DetalleRutina';
import { AuthStack } from './AuthStack';
import { Tabs } from './Tabs';
import { MainStackParamList } from './types';

// Flag TEMPORAL: true muestra Login y Registro; false muestra las pestañas.
// En la tanda 2 se reemplaza por el estado de useAuth.
const MOSTRAR_AUTH: boolean = true;

const Stack = createNativeStackNavigator<MainStackParamList>();

// Stack principal: las pestañas y las pantallas que se abren encima de ellas.
const MainStack = () => {
    return (
        <Stack.Navigator>
            {/* Las pestañas ya tienen su propio encabezado. */}
            <Stack.Screen name="Tabs" component={Tabs} options={{ headerShown: false }} />
            <Stack.Screen
                name="DetalleRutina"
                component={DetalleRutina}
                options={{ title: 'Detalle de rutina' }}
            />
            <Stack.Screen
                name="CrearRutina"
                component={CrearRutina}
                options={{ title: 'Crear rutina' }}
            />
            <Stack.Screen
                name="EntrenamientoActivo"
                component={EntrenamientoActivo}
                options={{ title: 'Entrenamiento activo' }}
            />
            <Stack.Screen name="Resumen" component={Resumen} />
            <Stack.Screen
                name="DetalleEntrenamiento"
                component={DetalleEntrenamiento}
                options={{ title: 'Detalle de entrenamiento' }}
            />
            <Stack.Screen
                name="RegistrarMedicion"
                component={RegistrarMedicion}
                options={{ title: 'Registrar medición' }}
            />
            <Stack.Screen
                name="CompararMediciones"
                component={CompararMediciones}
                options={{ title: 'Comparar mediciones' }}
            />
        </Stack.Navigator>
    );
};

// RootNavigator: decide qué parte de la app se muestra.
export const RootNavigator = () => {
    return MOSTRAR_AUTH ? <AuthStack /> : <MainStack />;
};
