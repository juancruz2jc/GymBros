import { Ionicons } from '@expo/vector-icons';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Historial } from '../screens/historial/Historial';
import { Inicio } from '../screens/inicio/Inicio';
import { Perfil } from '../screens/perfil/Perfil';
import { Progreso } from '../screens/progreso/Progreso';
import { Rutinas } from '../screens/rutinas/Rutinas';
import { theme } from '../theme/theme';
import { TabsParamList } from './types';

const Tab = createBottomTabNavigator<TabsParamList>();

// Icono de Ionicons que le corresponde a cada pestaña.
const ICONOS: Record<keyof TabsParamList, keyof typeof Ionicons.glyphMap> = {
    Inicio: 'home',
    Rutinas: 'barbell',
    Progreso: 'stats-chart',
    Historial: 'time',
    Perfil: 'person',
};

// Tabs: las cinco pestañas inferiores de la app.
export const Tabs = () => {
    return (
        <Tab.Navigator
            screenOptions={({ route }) => ({
                tabBarActiveTintColor: theme.colors.primary,
                tabBarInactiveTintColor: theme.colors.textMuted,
                tabBarIcon: ({ color, size }) => (
                    <Ionicons name={ICONOS[route.name]} color={color} size={size} />
                ),
            })}
        >
            {/* Inicio no lleva encabezado: empieza directamente con el saludo. */}
            <Tab.Screen name="Inicio" component={Inicio} options={{ headerShown: false }} />
            <Tab.Screen name="Rutinas" component={Rutinas} />
            <Tab.Screen name="Progreso" component={Progreso} />
            <Tab.Screen name="Historial" component={Historial} />
            <Tab.Screen name="Perfil" component={Perfil} />
        </Tab.Navigator>
    );
};
