import { Ionicons } from '@expo/vector-icons';
import { RouteProp, useNavigation, useRoute } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
    ActivityIndicator,
    Alert,
    Image,
    Modal,
    Pressable,
    StyleSheet,
    Text,
    View,
} from 'react-native';
import { FormScroll } from '../../components/FormScroll';
import { Input } from '../../components/Input';
import { Screen } from '../../components/Screen';
import { StyledButton } from '../../components/StyledButton';
import { useEjercicios } from '../../hooks/useEjercicios';
import { MainStackParamList } from '../../navigation/types';
import { getErrorMessage } from '../../services/api';
import {
    actualizarRutina,
    crearRutina,
    obtenerRutinaPorId,
} from '../../services/rutinaService';
import { theme } from '../../theme/theme';
import { Ejercicio } from '../../types/ejercicio';
import { CatalogoEjercicios } from './CatalogoEjercicios';

type CrearRutinaRouteProp = RouteProp<MainStackParamList, 'CrearRutina'>;
type NavigationProp = NativeStackNavigationProp<MainStackParamList>;

interface EjercicioConfigurado {
    ejercicio_id: string;
    nombre_es: string;
    gif_url: string | null;
    series_objetivo: number;
    repeticiones_objetivo: number;
    descanso_segundos: number;
}

const LIMITES = {
    series: { min: 1, max: 20, step: 1 },
    reps: { min: 1, max: 100, step: 1 },
    descanso: { min: 15, max: 300, step: 15 },
};

export const CrearRutina = () => {
    const navigation = useNavigation<NavigationProp>();
    const route = useRoute<CrearRutinaRouteProp>();
    const rutinaId = route.params?.rutinaId;
    const esEdicion = Boolean(rutinaId);

    const { ejercicios: catalogoEjercicios, cargando: cargandoCatalogo } = useEjercicios();

    const [nombre, setNombre] = useState<string>('');
    const [favorita, setFavorita] = useState<boolean>(false);
    const [ejerciciosSeleccionados, setEjerciciosSeleccionados] = useState<
        EjercicioConfigurado[]
    >([]);

    const [cargandoRutina, setCargandoRutina] = useState<boolean>(esEdicion);
    const [guardando, setGuardando] = useState<boolean>(false);
    const [selectorVisible, setSelectorVisible] = useState<boolean>(false);
    const [errorNombre, setErrorNombre] = useState<string>('');

    useEffect(() => {
        navigation.setOptions({
            title: esEdicion ? 'Editar rutina' : 'Nueva rutina',
        });
    }, [navigation, esEdicion]);

    // Si es edición, carga la rutina actual y cruza sus ejercicios con el catálogo
    const cargarRutinaEdicion = useCallback(async () => {
        if (!rutinaId || cargandoCatalogo) return;
        setCargandoRutina(true);
        try {
            const rutina = await obtenerRutinaPorId(rutinaId);
            setNombre(rutina.nombre);
            setFavorita(rutina.favorita);

            const mapaCatalogo = new Map(catalogoEjercicios.map((e) => [e.id, e]));
            const ordenados = [...rutina.ejercicios]
                .sort((a, b) => a.orden - b.orden)
                .map((item) => {
                    const info = mapaCatalogo.get(item.ejercicio_id);
                    return {
                        ejercicio_id: item.ejercicio_id,
                        nombre_es: info?.nombre_es ?? 'Ejercicio',
                        gif_url: info?.gif_url ?? null,
                        series_objetivo: item.series_objetivo,
                        repeticiones_objetivo: item.repeticiones_objetivo,
                        descanso_segundos: item.descanso_segundos,
                    };
                });

            setEjerciciosSeleccionados(ordenados);
        } catch (err) {
            Alert.alert('Error', getErrorMessage(err), [
                { text: 'Volver', onPress: () => navigation.goBack() },
            ]);
        } finally {
            setCargandoRutina(false);
        }
    }, [rutinaId, cargandoCatalogo, catalogoEjercicios, navigation]);

    useEffect(() => {
        if (esEdicion) {
            cargarRutinaEdicion();
        }
    }, [esEdicion, cargarRutinaEdicion]);

    const handleAgregarEjercicio = (ejercicio: Ejercicio) => {
        const yaExiste = ejerciciosSeleccionados.some(
            (item) => item.ejercicio_id === ejercicio.id,
        );
        if (yaExiste) {
            Alert.alert('Ya agregado', `"${ejercicio.nombre_es}" ya está en esta rutina.`);
            return;
        }

        setEjerciciosSeleccionados((prev) => [
            ...prev,
            {
                ejercicio_id: ejercicio.id,
                nombre_es: ejercicio.nombre_es,
                gif_url: ejercicio.gif_url,
                series_objetivo: 3,
                repeticiones_objetivo: 12,
                descanso_segundos: 60,
            },
        ]);
        setSelectorVisible(false);
    };

    const handleQuitarEjercicio = (ejercicioId: string) => {
        setEjerciciosSeleccionados((prev) =>
            prev.filter((item) => item.ejercicio_id !== ejercicioId),
        );
    };

    const ajustarParametro = (
        ejercicioId: string,
        campo: 'series_objetivo' | 'repeticiones_objetivo' | 'descanso_segundos',
        delta: number,
    ) => {
        const regla =
            campo === 'series_objetivo'
                ? LIMITES.series
                : campo === 'repeticiones_objetivo'
                    ? LIMITES.reps
                    : LIMITES.descanso;

        setEjerciciosSeleccionados((prev) =>
            prev.map((item) => {
                if (item.ejercicio_id !== ejercicioId) return item;
                const nuevoValor = Math.min(
                    regla.max,
                    Math.max(regla.min, item[campo] + delta),
                );
                return { ...item, [campo]: nuevoValor };
            }),
        );
    };

    const nombreValido = useMemo(() => nombre.trim().length > 0, [nombre]);
    const puedeGuardar = nombreValido && ejerciciosSeleccionados.length > 0 && !guardando;

    const handleGuardar = async () => {
        const nombreLimpio = nombre.trim();
        if (!nombreLimpio) {
            setErrorNombre('El nombre de la rutina es obligatorio');
            return;
        }
        setErrorNombre('');

        if (ejerciciosSeleccionados.length === 0) {
            Alert.alert('Faltan ejercicios', 'Agrega al menos un ejercicio a la rutina.');
            return;
        }

        setGuardando(true);
        try {
            const payload = {
                nombre: nombreLimpio,
                favorita,
                ejercicios: ejerciciosSeleccionados.map((item, idx) => ({
                    ejercicio_id: item.ejercicio_id,
                    orden: idx + 1,
                    series_objetivo: item.series_objetivo,
                    repeticiones_objetivo: item.repeticiones_objetivo,
                    descanso_segundos: item.descanso_segundos,
                })),
            };

            if (esEdicion && rutinaId) {
                await actualizarRutina(rutinaId, payload);
            } else {
                await crearRutina(payload);
            }

            navigation.goBack();
        } catch (err) {
            Alert.alert('Error al guardar', getErrorMessage(err));
        } finally {
            setGuardando(false);
        }
    };

    if (cargandoRutina) {
        return (
            <Screen>
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="large" color={theme.colors.primary} />
                </View>
            </Screen>
        );
    }

    return (
        <Screen>
            <FormScroll>
                <View style={styles.formSection}>
                    <Input
                        label="Nombre de la rutina"
                        placeholder="Ej. Tren superior - Fuerza"
                        value={nombre}
                        onChangeText={(texto) => {
                            setNombre(texto);
                            if (errorNombre && texto.trim().length > 0) {
                                setErrorNombre('');
                            }
                        }}
                        error={errorNombre}
                    />
                </View>

                <View style={styles.sectionHeader}>
                    <Text style={styles.sectionTitle}>
                        Ejercicios ({ejerciciosSeleccionados.length})
                    </Text>

                    <Pressable
                        style={({ pressed }) => [
                            styles.addExerciseBtn,
                            pressed && styles.pressed,
                        ]}
                        onPress={() => setSelectorVisible(true)}
                    >
                        <Ionicons name="add" size={18} color="#FFFFFF" />
                        <Text style={styles.addExerciseBtnText}>Agregar ejercicio</Text>
                    </Pressable>
                </View>

                {ejerciciosSeleccionados.length === 0 ? (
                    <View style={styles.emptyBox}>
                        <Ionicons
                            name="barbell-outline"
                            size={32}
                            color={theme.colors.primary}
                        />
                        <Text style={styles.emptyTitle}>Sin ejercicios seleccionados</Text>
                        <Text style={styles.emptySubtitle}>
                            Toca "Agregar ejercicio" para elegir desde el catálogo.
                        </Text>
                    </View>
                ) : (
                    ejerciciosSeleccionados.map((item, index) => (
                        <View key={item.ejercicio_id} style={styles.exerciseCard}>
                            <View style={styles.exerciseTopRow}>
                                <View style={styles.orderBadge}>
                                    <Text style={styles.orderBadgeText}>{index + 1}</Text>
                                </View>

                                {item.gif_url ? (
                                    <Image
                                        source={{ uri: item.gif_url }}
                                        style={styles.thumb}
                                        resizeMode="cover"
                                    />
                                ) : (
                                    <View style={styles.thumbPlaceholder}>
                                        <Ionicons
                                            name="barbell-outline"
                                            size={18}
                                            color={theme.colors.primary}
                                        />
                                    </View>
                                )}

                                <Text style={styles.exerciseName} numberOfLines={2}>
                                    {item.nombre_es}
                                </Text>

                                <Pressable
                                    onPress={() => handleQuitarEjercicio(item.ejercicio_id)}
                                    hitSlop={10}
                                    accessibilityLabel={`Quitar ${item.nombre_es}`}
                                >
                                    <Ionicons
                                        name="trash-outline"
                                        size={20}
                                        color={theme.colors.danger}
                                    />
                                </Pressable>
                            </View>

                            {/* Controles +/- con límites */}
                            <View style={styles.steppersRow}>
                                {/* Series */}
                                <View style={styles.stepperBox}>
                                    <Text style={styles.stepperLabel}>Series</Text>
                                    <View style={styles.stepperControls}>
                                        <Pressable
                                            style={styles.stepBtn}
                                            onPress={() =>
                                                ajustarParametro(
                                                    item.ejercicio_id,
                                                    'series_objetivo',
                                                    -LIMITES.series.step,
                                                )
                                            }
                                            disabled={item.series_objetivo <= LIMITES.series.min}
                                        >
                                            <Ionicons
                                                name="remove"
                                                size={16}
                                                color={theme.colors.text}
                                            />
                                        </Pressable>
                                        <Text style={styles.stepperValue}>
                                            {item.series_objetivo}
                                        </Text>
                                        <Pressable
                                            style={styles.stepBtn}
                                            onPress={() =>
                                                ajustarParametro(
                                                    item.ejercicio_id,
                                                    'series_objetivo',
                                                    LIMITES.series.step,
                                                )
                                            }
                                            disabled={item.series_objetivo >= LIMITES.series.max}
                                        >
                                            <Ionicons
                                                name="add"
                                                size={16}
                                                color={theme.colors.text}
                                            />
                                        </Pressable>
                                    </View>
                                </View>

                                {/* Repeticiones */}
                                <View style={styles.stepperBox}>
                                    <Text style={styles.stepperLabel}>Reps</Text>
                                    <View style={styles.stepperControls}>
                                        <Pressable
                                            style={styles.stepBtn}
                                            onPress={() =>
                                                ajustarParametro(
                                                    item.ejercicio_id,
                                                    'repeticiones_objetivo',
                                                    -LIMITES.reps.step,
                                                )
                                            }
                                            disabled={
                                                item.repeticiones_objetivo <= LIMITES.reps.min
                                            }
                                        >
                                            <Ionicons
                                                name="remove"
                                                size={16}
                                                color={theme.colors.text}
                                            />
                                        </Pressable>
                                        <Text style={styles.stepperValue}>
                                            {item.repeticiones_objetivo}
                                        </Text>
                                        <Pressable
                                            style={styles.stepBtn}
                                            onPress={() =>
                                                ajustarParametro(
                                                    item.ejercicio_id,
                                                    'repeticiones_objetivo',
                                                    LIMITES.reps.step,
                                                )
                                            }
                                            disabled={
                                                item.repeticiones_objetivo >= LIMITES.reps.max
                                            }
                                        >
                                            <Ionicons
                                                name="add"
                                                size={16}
                                                color={theme.colors.text}
                                            />
                                        </Pressable>
                                    </View>
                                </View>

                                {/* Descanso */}
                                <View style={styles.stepperBox}>
                                    <Text style={styles.stepperLabel}>Descanso</Text>
                                    <View style={styles.stepperControls}>
                                        <Pressable
                                            style={styles.stepBtn}
                                            onPress={() =>
                                                ajustarParametro(
                                                    item.ejercicio_id,
                                                    'descanso_segundos',
                                                    -LIMITES.descanso.step,
                                                )
                                            }
                                            disabled={
                                                item.descanso_segundos <= LIMITES.descanso.min
                                            }
                                        >
                                            <Ionicons
                                                name="remove"
                                                size={16}
                                                color={theme.colors.text}
                                            />
                                        </Pressable>
                                        <Text style={styles.stepperValue}>
                                            {item.descanso_segundos}s
                                        </Text>
                                        <Pressable
                                            style={styles.stepBtn}
                                            onPress={() =>
                                                ajustarParametro(
                                                    item.ejercicio_id,
                                                    'descanso_segundos',
                                                    LIMITES.descanso.step,
                                                )
                                            }
                                            disabled={
                                                item.descanso_segundos >= LIMITES.descanso.max
                                            }
                                        >
                                            <Ionicons
                                                name="add"
                                                size={16}
                                                color={theme.colors.text}
                                            />
                                        </Pressable>
                                    </View>
                                </View>
                            </View>
                        </View>
                    ))
                )}

                <View style={styles.submitContainer}>
                    <StyledButton
                        label={
                            guardando
                                ? 'Guardando...'
                                : esEdicion
                                    ? 'Guardar cambios'
                                    : 'Guardar rutina'
                        }
                        handleClick={handleGuardar}
                        disabled={!puedeGuardar}
                    />
                </View>
            </FormScroll>

            {/* Modal selector usando el catálogo de FE-06 con onSelect */}
            <Modal
                visible={selectorVisible}
                animationType="slide"
                onRequestClose={() => setSelectorVisible(false)}
            >
                <View style={styles.modalHeader}>
                    <Text style={styles.modalHeaderTitle}>Seleccionar ejercicio</Text>
                    <Pressable
                        onPress={() => setSelectorVisible(false)}
                        hitSlop={12}
                        style={styles.closeModalBtn}
                    >
                        <Ionicons name="close" size={24} color={theme.colors.text} />
                    </Pressable>
                </View>
                <CatalogoEjercicios onSelectEjercicio={handleAgregarEjercicio} />
            </Modal>
        </Screen>
    );
};

const styles = StyleSheet.create({
    loadingContainer: {
        alignItems: 'center',
        flex: 1,
        justifyContent: 'center',
    },
    formSection: {
        marginBottom: theme.spacing.md,
    },
    sectionHeader: {
        alignItems: 'center',
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: theme.spacing.md,
    },
    sectionTitle: {
        color: theme.colors.text,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
    },
    addExerciseBtn: {
        alignItems: 'center',
        backgroundColor: theme.colors.primary,
        borderRadius: 20,
        flexDirection: 'row',
        gap: 4,
        paddingHorizontal: 14,
        paddingVertical: 8,
    },
    addExerciseBtnText: {
        color: '#FFFFFF',
        fontSize: theme.fontSize.sm,
        fontWeight: 'bold',
    },
    pressed: {
        opacity: 0.8,
    },
    emptyBox: {
        alignItems: 'center',
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 16,
        borderStyle: 'dashed',
        borderWidth: 1,
        gap: theme.spacing.xs,
        marginBottom: theme.spacing.lg,
        padding: theme.spacing.xl,
    },
    emptyTitle: {
        color: theme.colors.text,
        fontSize: theme.fontSize.md,
        fontWeight: 'bold',
        marginTop: 4,
    },
    emptySubtitle: {
        color: theme.colors.textMuted,
        fontSize: theme.fontSize.sm,
        textAlign: 'center',
    },
    exerciseCard: {
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 16,
        borderWidth: 1,
        gap: theme.spacing.md,
        marginBottom: theme.spacing.md,
        padding: theme.spacing.md,
    },
    exerciseTopRow: {
        alignItems: 'center',
        flexDirection: 'row',
        gap: theme.spacing.sm,
    },
    orderBadge: {
        alignItems: 'center',
        backgroundColor: '#1E1B18',
        borderRadius: 11,
        height: 22,
        justifyContent: 'center',
        width: 22,
    },
    orderBadgeText: {
        color: '#FFFFFF',
        fontSize: 11,
        fontWeight: 'bold',
    },
    thumb: {
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 10,
        height: 44,
        width: 44,
    },
    thumbPlaceholder: {
        alignItems: 'center',
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 10,
        height: 44,
        justifyContent: 'center',
        width: 44,
    },
    exerciseName: {
        color: theme.colors.text,
        flex: 1,
        fontSize: theme.fontSize.md,
        fontWeight: 'bold',
    },
    steppersRow: {
        flexDirection: 'row',
        gap: theme.spacing.sm,
        justifyContent: 'space-between',
    },
    stepperBox: {
        alignItems: 'center',
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 12,
        flex: 1,
        gap: 6,
        paddingVertical: 8,
    },
    stepperLabel: {
        color: theme.colors.textMuted,
        fontSize: 11,
        fontWeight: '600',
    },
    stepperControls: {
        alignItems: 'center',
        flexDirection: 'row',
        gap: 8,
    },
    stepBtn: {
        alignItems: 'center',
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 12,
        borderWidth: 1,
        height: 26,
        justifyContent: 'center',
        width: 26,
    },
    stepperValue: {
        color: theme.colors.text,
        fontSize: 13,
        fontWeight: 'bold',
        minWidth: 28,
        textAlign: 'center',
    },
    submitContainer: {
        marginTop: theme.spacing.sm,
        paddingBottom: theme.spacing.lg,
    },
    modalHeader: {
        alignItems: 'center',
        backgroundColor: theme.colors.surface,
        borderBottomColor: theme.colors.border,
        borderBottomWidth: 1,
        flexDirection: 'row',
        justifyContent: 'space-between',
        paddingHorizontal: theme.spacing.lg,
        paddingVertical: theme.spacing.md,
    },
    modalHeaderTitle: {
        color: theme.colors.text,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
    },
    closeModalBtn: {
        padding: 4,
    },
});