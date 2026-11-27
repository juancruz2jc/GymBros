import { useNavigation } from '@react-navigation/native';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { ActionButton } from '../../components/ActionButton';
import { Card } from '../../components/Card';
import { Loading } from '../../components/Loading';
import { Screen } from '../../components/Screen';
import { Stars } from '../../components/Stars';
import { StyledButton } from '../../components/StyledButton';
import { useAuth } from '../../hooks/useAuth';
import { useInicio } from '../../hooks/useInicio';
import { theme } from '../../theme/theme';
import { formatearDiaYMes, formatearDuracion, formatearFecha } from '../../utils/formato';

// Inicio: saludo, acción principal, último entrenamiento y última medición
// (GYM-186).
export const Inicio = () => {
    const { usuario } = useAuth();
    const navigation = useNavigation();
    const {
        sesionActiva,
        rutinaFavorita,
        ultimoEntrenamiento,
        ultimaMedicion,
        esUsuarioNuevo,
        cargando,
        creando,
        error,
        errorInicio,
        recargar,
        iniciarEntrenamiento,
    } = useInicio();

    const abrirEntrenamiento = (sesionId: string) => {
        navigation.navigate('EntrenamientoActivo', { sesionId });
    };

    const empezar = async () => {
        const sesionId = await iniciarEntrenamiento();
        if (sesionId) {
            abrirEntrenamiento(sesionId);
        }
    };

    // El botón grande depende de la situación de la persona.
    const botonPrincipal = () => {
        if (sesionActiva) {
            return (
                <ActionButton
                    title="Continuar entrenamiento"
                    handleClick={() => abrirEntrenamiento(sesionActiva.id)}
                />
            );
        }
        if (esUsuarioNuevo) {
            return (
                <ActionButton
                    title="Crear mi primera rutina"
                    subtitle="Elige ejercicios del catálogo de GymBros"
                    handleClick={() => navigation.navigate('Tabs', { screen: 'Rutinas' })}
                />
            );
        }
        return (
            <ActionButton
                title="Iniciar entrenamiento"
                subtitle={rutinaFavorita ? `${rutinaFavorita.nombre} · tu rutina favorita` : ''}
                handleClick={empezar}
                disabled={creando}
            />
        );
    };

    if (cargando) {
        return (
            <Screen>
                <Loading />
            </Screen>
        );
    }

    return (
        <Screen>
            <ScrollView>
                <Text style={styles.greeting}>Hola, {usuario?.nombre}</Text>

                {error !== '' ? (
                    // Sin datos no se ofrece iniciar: podría haber una sesión activa.
                    <View style={styles.errorBlock}>
                        <Text style={styles.error}>{error}</Text>
                        <StyledButton label="Reintentar" handleClick={recargar} />
                    </View>
                ) : (
                    <>
                        <Text style={styles.subtitle}>
                            {esUsuarioNuevo
                                ? 'Empecemos con tu primer entrenamiento.'
                                : '¿Listo para entrenar hoy?'}
                        </Text>

                        {botonPrincipal()}
                        {errorInicio !== '' && <Text style={styles.error}>{errorInicio}</Text>}

                        <Card title="Último entrenamiento">
                            {ultimoEntrenamiento ? (
                                <View style={styles.row}>
                                    <View style={styles.grow}>
                                        <Text style={styles.name}>
                                            {ultimoEntrenamiento.rutina_nombre}
                                        </Text>
                                        <Text style={styles.detail}>
                                            {formatearDiaYMes(ultimoEntrenamiento.iniciada_en)}
                                            {ultimoEntrenamiento.duracion_segundos !== null &&
                                                ` · ${formatearDuracion(ultimoEntrenamiento.duracion_segundos)}`}
                                        </Text>
                                    </View>
                                    {/* Calificar es opcional: sin nota no hay estrellas. */}
                                    {ultimoEntrenamiento.calificacion !== null && (
                                        <Stars value={ultimoEntrenamiento.calificacion} />
                                    )}
                                </View>
                            ) : (
                                <Text style={styles.empty}>
                                    Aún no has entrenado. Tu primera sesión aparecerá aquí.
                                </Text>
                            )}
                        </Card>

                        <Card title="Última medición">
                            {ultimaMedicion ? (
                                <View style={styles.measure}>
                                    <Text style={styles.weight}>{ultimaMedicion.peso_kg} kg</Text>
                                    <Text style={styles.detail}>
                                        {formatearFecha(ultimaMedicion.fecha)}
                                    </Text>
                                </View>
                            ) : (
                                <>
                                    <Text style={styles.empty}>
                                        Aún no registras mediciones. Empieza con tu peso actual.
                                    </Text>
                                    <StyledButton
                                        label="Registrar medición"
                                        handleClick={() => navigation.navigate('RegistrarMedicion')}
                                    />
                                </>
                            )}
                        </Card>
                    </>
                )}
            </ScrollView>
        </Screen>
    );
};

const styles = StyleSheet.create({
    greeting: {
        color: theme.colors.text,
        fontSize: theme.fontSize.xl,
        fontWeight: 'bold',
        marginTop: theme.spacing.md,
    },
    subtitle: {
        color: theme.colors.textMuted,
        fontSize: theme.fontSize.sm,
        marginBottom: theme.spacing.lg,
    },
    errorBlock: { gap: theme.spacing.md, marginVertical: theme.spacing.lg },
    error: {
        color: theme.colors.error,
        fontSize: theme.fontSize.sm,
        marginBottom: theme.spacing.md,
    },
    row: { flexDirection: 'row', alignItems: 'center', gap: theme.spacing.sm },
    grow: { flex: 1 },
    name: {
        color: theme.colors.text,
        fontSize: theme.fontSize.md,
        fontWeight: 'bold',
    },
    detail: { color: theme.colors.textMuted, fontSize: theme.fontSize.sm },
    measure: { flexDirection: 'row', alignItems: 'baseline', gap: theme.spacing.sm },
    weight: {
        color: theme.colors.text,
        fontSize: theme.fontSize.xl,
        fontWeight: 'bold',
    },
    empty: {
        color: theme.colors.text,
        fontSize: theme.fontSize.sm,
        marginBottom: theme.spacing.sm,
    },
});
