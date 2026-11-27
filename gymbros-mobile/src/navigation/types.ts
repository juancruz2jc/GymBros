import { NavigatorScreenParams } from '@react-navigation/native';
import { Ejercicio } from '../types/ejercicio';

// Pantallas sin sesión iniciada.
export type AuthStackParamList = {
    Login: undefined;
    Registro: undefined;
};

// Pestañas inferiores.
export type TabsParamList = {
    Inicio: undefined;
    Rutinas: undefined;
    Progreso: undefined;
    Historial: undefined;
    Perfil: undefined;
};

// Stack principal: contiene las pestañas y las pantallas que se abren encima.
export type MainStackParamList = {
    Tabs: NavigatorScreenParams<TabsParamList> | undefined;
    CatalogoEjercicios: undefined;
    DetalleEjercicio: { ejercicio: Ejercicio };
    DetalleRutina: { rutinaId: string };
    // Sin rutinaId crea una rutina nueva; con rutinaId la edita.
    CrearRutina: { rutinaId?: string } | undefined;
    EntrenamientoActivo: { sesionId: string };
    Resumen: { sesionId: string };
    DetalleEntrenamiento: { sesionId: string };
    // Sin medicionId registra una medición nueva; con medicionId la edita.
    RegistrarMedicion: { medicionId?: string } | undefined;
    CompararMediciones: undefined;
};

// Hace que useNavigation() conozca los nombres y parámetros de las rutas.
declare global {
    namespace ReactNavigation {
        interface RootParamList extends MainStackParamList, AuthStackParamList { }
    }
}