import { Ionicons } from '@expo/vector-icons';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
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
    Inicio: 'home-outline',
    Rutinas: 'document-text-outline',
    Progreso: 'trending-up-outline',
    Historial: 'time-outline',
    Perfil: 'person-outline',
};

const ALTO_BARRA = 68;

// Tabs: las cinco pestañas inferiores de la app, en una barra redondeada.
export const Tabs = () => {
    // Espacio que ocupan los botones o gestos del sistema en la parte de abajo.
    const insets = useSafeAreaInsets();

    return (
        <Tab.Navigator
            screenOptions={({ route }) => ({
                // La pestaña activa se resalta con el color principal.
                tabBarActiveTintColor: theme.colors.primary,
                tabBarInactiveTintColor: theme.colors.textMuted,
                tabBarActiveBackgroundColor: theme.colors.primarySoft,
                // La barra: fondo claro, bordes redondos y separada de los lados.
                tabBarStyle: {
                    backgroundColor: theme.colors.card,
                    borderColor: theme.colors.border,
                    borderTopColor: theme.colors.border,
                    borderWidth: 1,
                    borderTopWidth: 1,
                    borderRadius: ALTO_BARRA / 2,
                    height: ALTO_BARRA,
                    marginHorizontal: theme.spacing.md,
                    marginBottom: insets.bottom + theme.spacing.sm,
                    paddingBottom: 0, // el margen ya deja libre la zona del sistema
                    paddingHorizontal: theme.spacing.sm,
                },
                // Cada pestaña: ícono arriba y texto abajo, con fondo redondeado.
                tabBarItemStyle: {
                    borderRadius: ALTO_BARRA / 2,
                    marginVertical: theme.spacing.xs,
                    overflow: 'hidden',
                },
                tabBarLabelPosition: 'below-icon',
                tabBarLabelStyle: { fontSize: 11, fontWeight: 'bold' },
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
