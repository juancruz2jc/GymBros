# GymBros Mobile

App móvil del deportista, hecha con Expo (SDK 58), React Native y TypeScript.
Consume la API de `gymbros-api/`.

## Requisitos

- Node.js 22.
- En el celular, la app **Expo Go** actualizada.

## Instalación

Desde `gymbros-mobile/`:

```powershell
npm install
Copy-Item .env.example .env     # en Mac o Linux: cp .env.example .env
```

El `.env` no se sube al repositorio. Contiene la URL de la API:

```
EXPO_PUBLIC_API_URL=https://gymbros-dev.apolobyte.online/api/v1
```

Las variables `EXPO_PUBLIC_*` quedan visibles dentro de la app, así que **no se
ponen secretos**. Si cambias el `.env`, vuelve a arrancar Expo.

## Arrancar

```powershell
npx expo start --tunnel
```

El modo `--tunnel` permite abrir la app aunque el celular y el computador no
estén en la misma red. Usa `@expo/ngrok`, que ya viene en las dependencias de
desarrollo (`npm install` lo instala).

| Dónde probar | Cómo |
|---|---|
| iPhone | Inicia sesión con la **misma cuenta de Expo** en el computador (`npx expo login`) y en Expo Go. Luego escanea el QR con la cámara |
| Android | Escanea el QR desde Expo Go |
| Navegador | Presiona la tecla `w` en la terminal de Expo |

> **Web y la API:** el backend no tiene CORS habilitado, así que en el navegador
> se ven las pantallas, pero las llamadas a la API quedan bloqueadas. Para probar
> datos reales, usa el celular.

## Ver el login o las pestañas

Mientras no exista `useAuth`, un flag temporal en
`src/navigation/RootNavigator.tsx` decide qué se muestra:

```ts
const MOSTRAR_AUTH: boolean = true;   // Login y Registro
const MOSTRAR_AUTH: boolean = false;  // Pestañas y demás pantallas
```

No subas cambios a este flag en tu PR.

## Estructura

```
gymbros-mobile/
├── App.tsx               componente raíz: área segura y navegación
├── index.ts              registra App
└── src/
    ├── components/       componentes reutilizables
    ├── hooks/            hooks propios
    ├── navigation/       AuthStack, Tabs, RootNavigator y tipos de rutas
    ├── screens/          una carpeta por módulo
    │   ├── auth/
    │   ├── inicio/
    │   ├── rutinas/
    │   ├── progreso/
    │   ├── historial/
    │   ├── perfil/
    │   └── entrenamiento/
    ├── services/         llamadas a la API
    ├── theme/            colores, espaciados y tamaños de fuente
    └── types/            tipos compartidos
```

## Componentes base

| Componente | Para qué | Props |
|---|---|---|
| `Screen` | Contenedor de cada pantalla | `children` |
| `StyledButton` | Botón principal | `label`, `handleClick`, `color?`, `disabled?` |
| `FAB` | Botón flotante | `label`, `position?`, `color?`, `onPress?`, `onLongPress?` |
| `Input` | Campo de texto | `label`, `value`, `onChangeText`, `error?`, `secureTextEntry?` |
| `EmptyState` | Pantalla sin datos | `message`, `actionLabel?`, `onAction?` |
| `Loading` | Indicador de carga | `color?` |

## Navegación

Cada ruta y sus parámetros están tipados en `src/navigation/types.ts`.

```tsx
const navigation = useNavigation();
navigation.navigate('DetalleRutina', { rutinaId: rutina.id });
```

```tsx
const { params } = useRoute<RouteProp<MainStackParamList, 'DetalleRutina'>>();
```

Si una pantalla necesita otro parámetro, primero se agrega en `types.ts`.

## Convenciones

- Una rama por historia, creada desde `dev`: `feature/GYM-XX`.
- Commits pequeños con el formato `GYM-XX: descripción`.
- Componentes y pantallas con `export const`.
- Cada componente declara `interface Props`, desestructura sus props y define
  valores por defecto.
- Usar los componentes de `src/components` antes de crear uno nuevo.
- Colores, espaciados y fuentes salen de `src/theme/theme.ts`.
- Librerías nuevas con `npx expo install <paquete>`, para que la versión sea
  compatible con el SDK.
- Antes de abrir el PR: `npx tsc --noEmit`.
- El PR va hacia `dev`.

## Pantallas y responsables

Cada pantalla es hoy un texto con su nombre. Quien la tenga asignada reemplaza el
contenido del archivo y conserva el nombre del componente exportado.

| Ruta | Archivo (en `src/screens/`) | Parámetros | Responsable |
|---|---|---|---|
| Login | `auth/Login.tsx` | — | Juan David |
| Registro | `auth/Registro.tsx` | — | Juan David |
| Inicio | `inicio/Inicio.tsx` | — | Juan David |
| Rutinas | `rutinas/Rutinas.tsx` | — | Luis |
| DetalleRutina | `rutinas/DetalleRutina.tsx` | `rutinaId` | Luis |
| CrearRutina | `rutinas/CrearRutina.tsx` | `rutinaId?` | Luis |
| Progreso | `progreso/Progreso.tsx` | — | Karen |
| RegistrarMedicion | `progreso/RegistrarMedicion.tsx` | `medicionId?` | Karen |
| CompararMediciones | `progreso/CompararMediciones.tsx` | — | Karen |
| Perfil | `perfil/Perfil.tsx` | — | Karen |
| EntrenamientoActivo | `entrenamiento/EntrenamientoActivo.tsx` | `sesionId` | Juan José |
| Resumen | `entrenamiento/Resumen.tsx` | `sesionId` | Juan José |
| Historial | `historial/Historial.tsx` | — | Juan José |
| DetalleEntrenamiento | `historial/DetalleEntrenamiento.tsx` | `sesionId` | Juan José |
