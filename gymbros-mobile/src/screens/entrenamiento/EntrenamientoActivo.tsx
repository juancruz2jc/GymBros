import { Ionicons } from '@expo/vector-icons';
import { RouteProp, useNavigation, usePreventRemove, useRoute } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Alert, Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Card } from '../../components/Card';
import { Contador } from '../../components/Contador';
import { EmptyState } from '../../components/EmptyState';
import { Loading } from '../../components/Loading';
import { Screen } from '../../components/Screen';
import { StyledButton } from '../../components/StyledButton';
import { useEjercicios } from '../../hooks/useEjercicios';
import { construirLote, useSesionActiva } from '../../hooks/useSesionActiva';
import { MainStackParamList } from '../../navigation/types';
import { theme } from '../../theme/theme';
import { Ejercicio } from '../../types/ejercicio';
import { CatalogoEjercicios } from '../rutinas/CatalogoEjercicios';

type Ruta = RouteProp<MainStackParamList, 'EntrenamientoActivo'>;
type Navegacion = NativeStackNavigationProp<MainStackParamList>;

// Límites de los contadores: nunca negativos y dentro de lo que acepta la API.
const REPS_MIN = 0; // 0 = serie fallida
const REPS_MAX = 100;
const REPS_POR_DEFECTO = 10;
const PESO_MIN = 0; // 0 = peso corporal
const PESO_MAX = 999; // la columna admite hasta 999.99
const PASO_PESO = 2.5;

// "01:05:09" o "05:09", a partir de segundos.
const formatearCronometro = (segundos: number) => {
    const h = Math.floor(segundos / 3600);
    const m = Math.floor((segundos % 3600) / 60);
    const s = segundos % 60;
    const dos = (n: number) => String(n).padStart(2, '0');
    return h > 0 ? `${dos(h)}:${dos(m)}:${dos(s)}` : `${dos(m)}:${dos(s)}`;
};

// "20 kg" o "22.5 kg". Number() quita los ceros que sobran.
const formatearPeso = (kg: number) => `${Number(kg.toFixed(2))} kg`;

// EntrenamientoActivo: cronómetro, ejercicio actual y registro de series
// (GYM-193). Las series se guardan en el celular y se envían al finalizar.
export const EntrenamientoActivo = () => {
    const navigation = useNavigation<Navegacion>();
    const { sesionId } = useRoute<Ruta>().params;
    const { ejercicios: catalogo } = useEjercicios();
    const {
        nombreRutina,
        ejercicios,
        series,
        ultimos,
        tiempo,
        cargando,
        error,
        noActiva,
        finalizando,
        descartando,
        errorAccion,
        recargar,
        agregarEjercicio,
        agregarSerie,
        eliminarSerie,
        finalizar,
        descartar,
    } = useSesionActiva(sesionId);

    const [indiceActual, setIndiceActual] = useState(0);
    const [repeticiones, setRepeticiones] = useState(REPS_POR_DEFECTO);
    const [peso, setPeso] = useState(0);
    const [selectorVisible, setSelectorVisible] = useState(false);

    // Al finalizar o descartar se sale sin preguntar.
    const permitirSalida = useRef(false);

    const nombres = useMemo(
        () => new Map(catalogo.map((ejercicio) => [ejercicio.id, ejercicio.nombre_es])),
        [catalogo],
    );
    const nombreDe = (ejercicioId: string) => nombres.get(ejercicioId) ?? 'Ejercicio';

    const actual = ejercicios[indiceActual] ?? null;
    const ultimoActual = actual ? ultimos[actual.ejercicio_id] : undefined;
    const seriesActual = actual
        ? series.filter((serie) => serie.ejercicio_id === actual.ejercicio_id).length
        : 0;

    // Al cambiar de ejercicio (o cuando llega "la vez pasada") los contadores
    // empiezan con lo de la última vez o con el objetivo de la rutina.
    useEffect(() => {
        if (!actual) {
            return;
        }
        setRepeticiones(
            ultimoActual?.repeticiones_realizadas ?? actual.repeticiones_objetivo ?? REPS_POR_DEFECTO,
        );
        setPeso(ultimoActual?.peso_usado_kg ?? 0);
    }, [actual, ultimoActual]);

    // Salir con el botón atrás perdería las series que aún no se envían.
    usePreventRemove(series.length > 0, ({ data }) => {
        if (permitirSalida.current) {
            navigation.dispatch(data.action);
            return;
        }
        Alert.alert(
            '¿Salir del entrenamiento?',
            'La sesión seguirá activa, pero las series que registraste se perderán si no finalizas.',
            [
                { text: 'Quedarme', style: 'cancel' },
                {
                    text: 'Salir',
                    style: 'destructive',
                    onPress: () => navigation.dispatch(data.action),
                },
            ],
        );
    });

    const irAlResumen = () => {
        permitirSalida.current = true;
        navigation.replace('Resumen', { sesionId });
    };

    const irAlInicio = () => {
        permitirSalida.current = true;
        navigation.popToTop();
    };

    const seleccionarDelCatalogo = (ejercicio: Ejercicio) => {
        setSelectorVisible(false);
        setIndiceActual(agregarEjercicio(ejercicio.id));
    };

    const registrarSerie = () => {
        if (actual) {
            agregarSerie(actual.ejercicio_id, repeticiones, peso);
        }
    };

    const confirmarBorrado = (clave: string) => {
        Alert.alert('¿Borrar esta serie?', 'Se quitará de este entrenamiento.', [
            { text: 'Cancelar', style: 'cancel' },
            {
                text: 'Borrar',
                style: 'destructive',
                onPress: () => {
                    if (!eliminarSerie(clave)) {
                        Alert.alert(
                            'No se puede borrar',
                            'Las series ya se guardaron en el servidor. Termina de finalizar el entrenamiento.',
                        );
                    }
                },
            },
        ]);
    };

    const pedirFinalizar = () => {
        if (series.length === 0) {
            Alert.alert(
                '¿Finalizar sin series?',
                'No registraste ninguna serie. El entrenamiento se guardará vacío en tu historial.',
                [
                    { text: 'Cancelar', style: 'cancel' },
                    {
                        text: 'Finalizar',
                        onPress: async () => {
                            if ((await finalizar(true)) === 'ok') {
                                irAlResumen();
                            }
                        },
                    },
                ],
            );
            return;
        }
        Alert.alert(
            '¿Terminar el entrenamiento?',
            `Se guardarán ${series.length} ${series.length === 1 ? 'serie' : 'series'}.`,
            [
                { text: 'Seguir entrenando', style: 'cancel' },
                {
                    text: 'Finalizar',
                    onPress: async () => {
                        if ((await finalizar()) === 'ok') {
                            irAlResumen();
                        }
                    },
                },
            ],
        );
    };

    const pedirDescartar = () => {
        Alert.alert(
            '¿Descartar el entrenamiento?',
            'Se borrará la sesión con todas sus series. No se puede deshacer.',
            [
                { text: 'Cancelar', style: 'cancel' },
                {
                    text: 'Descartar',
                    style: 'destructive',
                    onPress: async () => {
                        if (await descartar()) {
                            irAlInicio();
                        }
                    },
                },
            ],
        );
    };

    if (cargando) {
        return (
            <Screen>
                <Loading />
            </Screen>
        );
    }

    if (error !== '') {
        return (
            <Screen>
                <EmptyState message={error} actionLabel="Reintentar" onAction={recargar} />
            </Screen>
        );
    }

    if (noActiva) {
        return (
            <Screen>
                <EmptyState
                    message="Este entrenamiento ya no está activo: se finalizó o se descartó."
                    actionLabel="Ir al inicio"
                    onAction={irAlInicio}
                />
            </Screen>
        );
    }

    // numero_serie de cada serie, igual al que se enviará a la API.
    const lote = construirLote(series);
    const ocupado = finalizando || descartando;

    return (
        <Screen>
            <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
                <View style={styles.header}>
                    <Text style={styles.rutina} numberOfLines={1}>
                        {nombreRutina}
                    </Text>
                    <View style={styles.cronometro}>
                        <Ionicons name="time-outline" size={20} color={theme.colors.primaryText} />
                        <Text style={styles.cronometroTexto} accessibilityLabel="Tiempo transcurrido">
                            {formatearCronometro(tiempo)}
                        </Text>
                    </View>
                </View>

                {/* Ejercicios de la sesión: se toca uno para registrarle series. */}
                <ScrollView
                    horizontal
                    showsHorizontalScrollIndicator={false}
                    contentContainerStyle={styles.chips}
                >
                    {ejercicios.map((ejercicio, indice) => {
                        const activo = indice === indiceActual;
                        return (
                            <Pressable
                                key={ejercicio.ejercicio_id}
                                onPress={() => setIndiceActual(indice)}
                                style={[styles.chip, activo && styles.chipActivo]}
                                accessibilityRole="button"
                                accessibilityState={{ selected: activo }}
                            >
                                <Text
                                    style={[styles.chipTexto, activo && styles.chipTextoActivo]}
                                    numberOfLines={1}
                                >
                                    {indice + 1}. {nombreDe(ejercicio.ejercicio_id)}
                                </Text>
                            </Pressable>
                        );
                    })}
                    <Pressable
                        onPress={() => setSelectorVisible(true)}
                        style={[styles.chip, styles.chipAgregar]}
                        accessibilityRole="button"
                    >
                        <Ionicons name="add" size={16} color={theme.colors.primaryText} />
                        <Text style={styles.chipTextoActivo}>Ejercicio</Text>
                    </Pressable>
                </ScrollView>

                {actual ? (
                    <Card title="Ejercicio actual">
                        <Text style={styles.nombreEjercicio}>{nombreDe(actual.ejercicio_id)}</Text>
                        {actual.series_objetivo !== null && (
                            <Text style={styles.detalle}>
                                Objetivo: {actual.series_objetivo} x {actual.repeticiones_objetivo}
                                {actual.descanso_segundos !== null &&
                                    ` · descanso ${actual.descanso_segundos}s`}
                                {`  ·  llevas ${seriesActual}`}
                            </Text>
                        )}
                        <Text style={styles.detalle}>
                            {ultimoActual === undefined
                                ? 'Buscando la vez pasada...'
                                : ultimoActual === null
                                  ? 'Primera vez con este ejercicio.'
                                  : `La vez pasada: ${formatearPeso(ultimoActual.peso_usado_kg)} x ${ultimoActual.repeticiones_realizadas}`}
                        </Text>

                        <View style={styles.contadores}>
                            <Contador
                                label="Repeticiones"
                                value={String(repeticiones)}
                                handleMenos={() => setRepeticiones((r) => Math.max(REPS_MIN, r - 1))}
                                handleMas={() => setRepeticiones((r) => Math.min(REPS_MAX, r + 1))}
                                puedeMenos={repeticiones > REPS_MIN}
                                puedeMas={repeticiones < REPS_MAX}
                            />
                            <Contador
                                label="Peso"
                                value={formatearPeso(peso)}
                                handleMenos={() => setPeso((p) => Math.max(PESO_MIN, p - PASO_PESO))}
                                handleMas={() => setPeso((p) => Math.min(PESO_MAX, p + PASO_PESO))}
                                puedeMenos={peso > PESO_MIN}
                                puedeMas={peso < PESO_MAX}
                            />
                        </View>

                        <StyledButton
                            label={`Registrar serie ${seriesActual + 1}`}
                            handleClick={registrarSerie}
                            disabled={ocupado}
                        />
                    </Card>
                ) : (
                    <Card title="Entrenamiento libre">
                        <Text style={styles.detalle}>
                            Agrega un ejercicio del catálogo para empezar a registrar series.
                        </Text>
                        <StyledButton
                            label="Agregar ejercicio"
                            handleClick={() => setSelectorVisible(true)}
                        />
                    </Card>
                )}

                <Card title={`Series registradas (${series.length})`}>
                    {series.length === 0 ? (
                        <Text style={styles.detalle}>Aún no registras series en esta sesión.</Text>
                    ) : (
                        <>
                            <Text style={styles.ayuda}>Mantén presionada una serie para borrarla.</Text>
                            {/* La más reciente arriba. */}
                            {[...series].reverse().map((serie) => {
                                const numero =
                                    lote[series.indexOf(serie)]?.numero_serie ?? 0;
                                return (
                                    <Pressable
                                        key={serie.clave}
                                        onLongPress={() => confirmarBorrado(serie.clave)}
                                        delayLongPress={400}
                                        style={({ pressed }) => [
                                            styles.serie,
                                            pressed && styles.seriePresionada,
                                        ]}
                                        accessibilityHint="Mantén presionado para borrar"
                                    >
                                        <Text style={styles.serieNombre} numberOfLines={1}>
                                            {nombreDe(serie.ejercicio_id)} · serie {numero}
                                        </Text>
                                        <Text style={styles.serieValor}>
                                            {serie.repeticiones_realizadas} x{' '}
                                            {formatearPeso(serie.peso_usado_kg)}
                                        </Text>
                                    </Pressable>
                                );
                            })}
                        </>
                    )}
                </Card>
            </ScrollView>

            <View style={styles.footer}>
                {errorAccion !== '' && <Text style={styles.error}>{errorAccion}</Text>}
                <StyledButton
                    label={finalizando ? 'Guardando...' : 'Finalizar entrenamiento'}
                    handleClick={pedirFinalizar}
                    disabled={ocupado}
                />
                <StyledButton
                    label={descartando ? 'Descartando...' : 'Descartar entrenamiento'}
                    color={theme.colors.error}
                    handleClick={pedirDescartar}
                    disabled={ocupado}
                />
            </View>

            {/* Selector de ejercicios: el mismo catálogo de FE-06, como en CrearRutina. */}
            <Modal
                visible={selectorVisible}
                animationType="slide"
                onRequestClose={() => setSelectorVisible(false)}
            >
                <View style={styles.modalHeader}>
                    <Text style={styles.modalTitulo}>Agregar ejercicio</Text>
                    <Pressable
                        onPress={() => setSelectorVisible(false)}
                        hitSlop={12}
                        accessibilityRole="button"
                        accessibilityLabel="Cerrar"
                    >
                        <Ionicons name="close" size={24} color={theme.colors.text} />
                    </Pressable>
                </View>
                <CatalogoEjercicios onSelectEjercicio={seleccionarDelCatalogo} />
            </Modal>
        </Screen>
    );
};

const styles = StyleSheet.create({
    content: { paddingBottom: theme.spacing.md },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: theme.spacing.sm,
        marginBottom: theme.spacing.md,
    },
    rutina: {
        flex: 1,
        color: theme.colors.text,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
    },
    cronometro: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: theme.spacing.xs,
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 20,
        paddingHorizontal: theme.spacing.md,
        paddingVertical: theme.spacing.sm,
    },
    cronometroTexto: {
        color: theme.colors.primaryText,
        fontSize: theme.fontSize.lg,
        fontVariant: ['tabular-nums'],
        fontWeight: 'bold',
    },
    chips: { gap: theme.spacing.sm, marginBottom: theme.spacing.md },
    chip: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: theme.spacing.xs,
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 20,
        borderWidth: 1,
        maxWidth: 200,
        paddingHorizontal: theme.spacing.md,
        paddingVertical: theme.spacing.sm,
    },
    chipActivo: {
        backgroundColor: theme.colors.primarySoft,
        borderColor: theme.colors.primary,
    },
    chipAgregar: { borderStyle: 'dashed' },
    chipTexto: { color: theme.colors.text, fontSize: theme.fontSize.sm },
    chipTextoActivo: {
        color: theme.colors.primaryText,
        fontSize: theme.fontSize.sm,
        fontWeight: 'bold',
    },
    nombreEjercicio: {
        color: theme.colors.text,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
    },
    detalle: { color: theme.colors.textMuted, fontSize: theme.fontSize.sm },
    contadores: {
        flexDirection: 'row',
        gap: theme.spacing.sm,
        marginVertical: theme.spacing.md,
    },
    ayuda: {
        color: theme.colors.textMuted,
        fontSize: 12,
        marginBottom: theme.spacing.xs,
    },
    serie: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: theme.spacing.sm,
        borderTopColor: theme.colors.border,
        borderTopWidth: 1,
        paddingVertical: theme.spacing.sm,
    },
    seriePresionada: { opacity: 0.6 },
    serieNombre: { flex: 1, color: theme.colors.text, fontSize: theme.fontSize.sm },
    serieValor: {
        color: theme.colors.text,
        fontSize: theme.fontSize.sm,
        fontWeight: 'bold',
    },
    footer: { gap: theme.spacing.sm, paddingTop: theme.spacing.sm },
    error: { color: theme.colors.error, fontSize: theme.fontSize.sm, textAlign: 'center' },
    modalHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        backgroundColor: theme.colors.background,
        paddingHorizontal: theme.spacing.md,
        paddingTop: theme.spacing.lg,
    },
    modalTitulo: {
        color: theme.colors.text,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
    },
});
