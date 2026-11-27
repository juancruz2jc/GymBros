import { Ionicons } from '@expo/vector-icons';
import { RouteProp, useNavigation, useRoute } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import axios from 'axios';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
    ActivityIndicator,
    Alert,
    FlatList,
    Image,
    Pressable,
    StyleSheet,
    Text,
    View,
} from 'react-native';
import { Screen } from '../../components/Screen';
import { useEjercicios } from '../../hooks/useEjercicios';
import { MainStackParamList } from '../../navigation/types';
import { getErrorMessage } from '../../services/api';
import { obtenerRutinaPorId } from '../../services/rutinaService';
import { iniciarSesion, obtenerSesionActiva } from '../../services/sesionService';
import { theme } from '../../theme/theme';
import { Rutina } from '../../types/rutina';
import { Sesion } from '../../types/sesion';

type DetalleRutinaRouteProp = RouteProp<MainStackParamList, 'DetalleRutina'>;
type NavigationProp = NativeStackNavigationProp<MainStackParamList>;

const generarIdempotencyKey = (rutinaId: string): string => {
    return `sesion-${rutinaId}-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;
};

export const DetalleRutina = () => {
    const navigation = useNavigation<NavigationProp>();
    const { params } = useRoute<DetalleRutinaRouteProp>();
    const { rutinaId } = params;

    const { ejercicios: catalogoEjercicios, cargando: cargandoCatalogo } = useEjercicios();

    const [rutina, setRutina] = useState<Rutina | null>(null);
    const [cargandoRutina, setCargandoRutina] = useState<boolean>(true);
    const [error, setError] = useState<string>('');
    const [iniciandoSesion, setIniciandoSesion] = useState<boolean>(false);
    const [sesionActiva, setSesionActiva] = useState<Sesion | null>(null);
    const [conflicto409, setConflicto409] = useState<boolean>(false);

    const idempotencyKeyRef = useRef<string>(generarIdempotencyKey(rutinaId));

    const cargarDetalle = useCallback(async () => {
        setCargandoRutina(true);
        setError('');
        try {
            const data = await obtenerRutinaPorId(rutinaId);
            setRutina(data);
        } catch (err) {
            if (axios.isAxiosError(err) && err.response?.status === 404) {
                Alert.alert('Rutina no encontrada', 'La rutina no existe', [
                    { text: 'Volver', onPress: () => navigation.goBack() },
                ]);
                return;
            }
            setError(getErrorMessage(err));
        } finally {
            setCargandoRutina(false);
        }
    }, [rutinaId, navigation]);

    useEffect(() => {
        cargarDetalle();
    }, [cargarDetalle]);

    // Ordenar por `orden` en el front y cruzar con useEjercicios
    const ejerciciosOrdenados = useMemo(() => {
        if (!rutina?.ejercicios) return [];

        const mapaCatalogo = new Map(catalogoEjercicios.map((ej) => [ej.id, ej]));

        return [...rutina.ejercicios]
            .sort((a, b) => a.orden - b.orden)
            .map((item) => ({
                ...item,
                detalle: mapaCatalogo.get(item.ejercicio_id),
            }));
    }, [rutina, catalogoEjercicios]);

    const handleIniciarEntrenamiento = async () => {
        if (iniciandoSesion || !rutina) return;

        setIniciandoSesion(true);
        setConflicto409(false);

        try {
            const nuevaSesion = await iniciarSesion({
                rutina_id: rutina.id,
                idempotency_key: idempotencyKeyRef.current,
            });
            idempotencyKeyRef.current = generarIdempotencyKey(rutina.id);
            navigation.navigate('EntrenamientoActivo', { sesionId: nuevaSesion.id });
        } catch (err) {
            if (axios.isAxiosError(err) && err.response?.status === 409) {
                setConflicto409(true);
                const activa = await obtenerSesionActiva();
                if (activa) {
                    setSesionActiva(activa);
                }
            } else {
                Alert.alert('Error', getErrorMessage(err));
            }
        } finally {
            setIniciandoSesion(false);
        }
    };

    const handleContinuarSesion = async () => {
        if (sesionActiva?.id) {
            navigation.navigate('EntrenamientoActivo', { sesionId: sesionActiva.id });
            return;
        }
        const activa = await obtenerSesionActiva();
        if (activa?.id) {
            navigation.navigate('EntrenamientoActivo', { sesionId: activa.id });
        }
    };

    const cargando = cargandoRutina || cargandoCatalogo;

    return (
        <Screen>
            <View style={styles.header}>
                <Pressable
                    onPress={() => navigation.goBack()}
                    hitSlop={12}
                    style={styles.backButton}
                >
                    <Ionicons name="chevron-back" size={24} color={theme.colors.text} />
                </Pressable>

                <View style={styles.headerCenter}>
                    <Text style={styles.headerTitle} numberOfLines={1}>
                        {rutina?.nombre ?? 'Detalle de rutina'}
                    </Text>
                    {!cargando && rutina && (
                        <Text style={styles.headerSubtitle}>
                            {ejerciciosOrdenados.length}{' '}
                            {ejerciciosOrdenados.length === 1 ? 'ejercicio' : 'ejercicios'}
                        </Text>
                    )}
                </View>

                <View style={styles.headerRightSpacer} />
            </View>

            {cargando ? (
                <View style={styles.skeletonList}>
                    {[1, 2, 3, 4].map((item) => (
                        <View key={item} style={styles.skeletonRow}>
                            <View style={styles.skeletonCircle} />
                            <View style={styles.skeletonThumb} />
                            <View style={styles.skeletonLines}>
                                <View style={styles.skeletonLineLg} />
                                <View style={styles.skeletonLineSm} />
                            </View>
                        </View>
                    ))}
                </View>
            ) : error !== '' ? (
                <View style={styles.centerState}>
                    <Ionicons name="wifi-outline" size={40} color={theme.colors.primary} />
                    <Text style={styles.errorTitle}>No se pudo cargar la rutina</Text>
                    <Text style={styles.errorSubtitle}>{error}</Text>
                    <Pressable style={styles.primaryButton} onPress={cargarDetalle}>
                        <Text style={styles.primaryButtonText}>Reintentar</Text>
                    </Pressable>
                </View>
            ) : (
                <>
                    <FlatList
                        data={ejerciciosOrdenados}
                        keyExtractor={(item) => item.id}
                        showsVerticalScrollIndicator={false}
                        contentContainerStyle={styles.listContent}
                        ListEmptyComponent={
                            <View style={styles.centerState}>
                                <Text style={styles.errorSubtitle}>
                                    Esta rutina aún no tiene ejercicios asignados.
                                </Text>
                            </View>
                        }
                        renderItem={({ item, index }) => (
                            <View style={styles.exerciseCard}>
                                <View style={styles.orderBadge}>
                                    <Text style={styles.orderBadgeText}>{index + 1}</Text>
                                </View>

                                {item.detalle?.gif_url ? (
                                    <Image
                                        source={{ uri: item.detalle.gif_url }}
                                        style={styles.exerciseThumb}
                                        resizeMode="cover"
                                    />
                                ) : (
                                    <View style={styles.exerciseThumbPlaceholder}>
                                        <Ionicons
                                            name="barbell-outline"
                                            size={20}
                                            color={theme.colors.primary}
                                        />
                                    </View>
                                )}

                                <View style={styles.exerciseInfo}>
                                    <Text style={styles.exerciseName} numberOfLines={1}>
                                        {item.detalle?.nombre_es ?? 'Ejercicio'}
                                    </Text>
                                    <Text style={styles.exerciseMeta}>
                                        <Text style={styles.seriesRepsText}>
                                            {item.series_objetivo} x {item.repeticiones_objetivo}
                                        </Text>
                                        {'  •  '}
                                        Descanso {item.descanso_segundos}s
                                    </Text>
                                </View>
                            </View>
                        )}
                    />

                    {conflicto409 && (
                        <View style={styles.conflictBanner}>
                            <View style={styles.conflictHeader}>
                                <Ionicons
                                    name="time-outline"
                                    size={18}
                                    color={theme.colors.primary}
                                />
                                <Text style={styles.conflictTitle}>
                                    Ya tienes un entrenamiento en curso
                                </Text>
                            </View>
                            <Text style={styles.conflictText}>
                                Termina o descarta tu sesión activa antes de iniciar una nueva.
                            </Text>
                            <Pressable
                                style={styles.continueSessionButton}
                                onPress={handleContinuarSesion}
                            >
                                <Text style={styles.continueSessionButtonText}>Continuar</Text>
                            </Pressable>
                        </View>
                    )}

                    <View style={styles.footer}>
                        <Pressable
                            style={({ pressed }) => [
                                styles.primaryButton,
                                (iniciandoSesion || ejerciciosOrdenados.length === 0) &&
                                styles.buttonDisabled,
                                pressed && !iniciandoSesion && styles.buttonPressed,
                            ]}
                            onPress={handleIniciarEntrenamiento}
                            disabled={iniciandoSesion || ejerciciosOrdenados.length === 0}
                        >
                            {iniciandoSesion ? (
                                <ActivityIndicator color="#FFFFFF" />
                            ) : (
                                <Text style={styles.primaryButtonText}>Iniciar entrenamiento</Text>
                            )}
                        </Pressable>
                    </View>
                </>
            )}
        </Screen>
    );
};

const styles = StyleSheet.create({
    header: {
        alignItems: 'center',
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: theme.spacing.lg,
    },
    backButton: {
        padding: 4,
        width: 32,
    },
    headerCenter: {
        alignItems: 'center',
        flex: 1,
    },
    headerTitle: {
        color: theme.colors.text,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
    },
    headerSubtitle: {
        color: theme.colors.textMuted,
        fontSize: 12,
        marginTop: 2,
    },
    headerRightSpacer: {
        width: 32,
    },
    listContent: {
        paddingBottom: theme.spacing.md,
    },
    exerciseCard: {
        alignItems: 'center',
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 16,
        borderWidth: 1,
        flexDirection: 'row',
        gap: theme.spacing.sm,
        marginBottom: theme.spacing.sm,
        padding: theme.spacing.sm,
    },
    orderBadge: {
        alignItems: 'center',
        backgroundColor: '#1E1B18',
        borderRadius: 12,
        height: 24,
        justifyContent: 'center',
        width: 24,
    },
    orderBadgeText: {
        color: '#FFFFFF',
        fontSize: 12,
        fontWeight: 'bold',
    },
    exerciseThumb: {
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 10,
        height: 48,
        width: 48,
    },
    exerciseThumbPlaceholder: {
        alignItems: 'center',
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 10,
        height: 48,
        justifyContent: 'center',
        width: 48,
    },
    exerciseInfo: {
        flex: 1,
        gap: 4,
    },
    exerciseName: {
        color: theme.colors.text,
        fontSize: theme.fontSize.md,
        fontWeight: 'bold',
    },
    exerciseMeta: {
        color: theme.colors.textMuted,
        fontSize: theme.fontSize.sm,
    },
    seriesRepsText: {
        color: theme.colors.primary,
        fontWeight: '700',
    },
    conflictBanner: {
        backgroundColor: '#1E1B18',
        borderRadius: 16,
        gap: theme.spacing.xs,
        marginBottom: theme.spacing.sm,
        padding: theme.spacing.md,
    },
    conflictHeader: {
        alignItems: 'center',
        flexDirection: 'row',
        gap: 8,
    },
    conflictTitle: {
        color: theme.colors.primary,
        fontSize: theme.fontSize.sm,
        fontWeight: 'bold',
    },
    conflictText: {
        color: '#E5E0D8',
        fontSize: 12,
        lineHeight: 18,
    },
    continueSessionButton: {
        alignItems: 'center',
        backgroundColor: theme.colors.primary,
        borderRadius: 20,
        marginTop: theme.spacing.xs,
        paddingVertical: 10,
    },
    continueSessionButtonText: {
        color: '#FFFFFF',
        fontSize: theme.fontSize.sm,
        fontWeight: 'bold',
    },
    footer: {
        paddingTop: theme.spacing.xs,
    },
    primaryButton: {
        alignItems: 'center',
        backgroundColor: theme.colors.primary,
        borderRadius: 24,
        justifyContent: 'center',
        minHeight: 48,
        paddingVertical: 14,
    },
    buttonDisabled: {
        opacity: 0.5,
    },
    buttonPressed: {
        opacity: 0.85,
    },
    primaryButtonText: {
        color: '#FFFFFF',
        fontSize: theme.fontSize.md,
        fontWeight: 'bold',
    },
    centerState: {
        alignItems: 'center',
        flex: 1,
        gap: theme.spacing.md,
        justifyContent: 'center',
        paddingHorizontal: theme.spacing.lg,
    },
    errorTitle: {
        color: theme.colors.text,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
    },
    errorSubtitle: {
        color: theme.colors.textMuted,
        fontSize: theme.fontSize.sm,
        textAlign: 'center',
    },
    skeletonList: {
        gap: theme.spacing.sm,
    },
    skeletonRow: {
        alignItems: 'center',
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 16,
        borderWidth: 1,
        flexDirection: 'row',
        gap: theme.spacing.sm,
        padding: theme.spacing.sm,
    },
    skeletonCircle: {
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 12,
        height: 24,
        width: 24,
    },
    skeletonThumb: {
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 10,
        height: 48,
        width: 48,
    },
    skeletonLines: {
        flex: 1,
        gap: 6,
    },
    skeletonLineLg: {
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 6,
        height: 14,
        width: '70%',
    },
    skeletonLineSm: {
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 6,
        height: 10,
        width: '45%',
    },
});