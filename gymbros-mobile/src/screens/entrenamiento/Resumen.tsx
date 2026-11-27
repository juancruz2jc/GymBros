import { Ionicons } from '@expo/vector-icons';
import { RouteProp, useNavigation, useRoute } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useLayoutEffect, useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';
import { Card } from '../../components/Card';
import { Estrellas } from '../../components/Estrellas';
import { FormScroll } from '../../components/FormScroll';
import { Loading } from '../../components/Loading';
import { Screen } from '../../components/Screen';
import { Stars } from '../../components/Stars';
import { StyledButton } from '../../components/StyledButton';
import { TextLink } from '../../components/TextLink';
import { useResumen } from '../../hooks/useResumen';
import { MainStackParamList } from '../../navigation/types';
import { theme } from '../../theme/theme';
import { formatearDiaYMes, formatearDuracion } from '../../utils/formato';

type Ruta = RouteProp<MainStackParamList, 'Resumen'>;
type Navegacion = NativeStackNavigationProp<MainStackParamList>;

const MAX_NOTA = 500;

// "1.250 kg": volumen redondeado, con punto de miles.
const formatearVolumen = (kg: number) =>
    `${String(Math.round(kg)).replace(/\B(?=(\d{3})+(?!\d))/g, '.')} kg`;

// Resumen: datos de la sesión recién finalizada y su calificación (GYM-194).
export const Resumen = () => {
    const navigation = useNavigation<Navegacion>();
    const { sesionId } = useRoute<Ruta>().params;
    const {
        sesion,
        volumenTotal,
        totalSeries,
        cargando,
        error,
        guardando,
        errorGuardar,
        estado,
        recargar,
        calificar,
        omitir,
    } = useResumen(sesionId);

    const [calificacion, setCalificacion] = useState(0); // 0 = aún no elige
    const [nota, setNota] = useState('');

    // La sesión ya se cerró: sin botón ni gesto para volver al entrenamiento.
    useLayoutEffect(() => {
        navigation.setOptions({
            title: 'Resumen',
            headerBackVisible: false,
            gestureEnabled: false,
        });
    }, [navigation]);

    const irAlInicio = () => navigation.popTo('Tabs', { screen: 'Inicio' });

    if (cargando) {
        return (
            <Screen>
                <Loading />
            </Screen>
        );
    }

    if (error !== '' || !sesion) {
        return (
            <Screen>
                <View style={styles.centro}>
                    <Text style={styles.error}>{error || 'No se encontró la sesión.'}</Text>
                    <StyledButton label="Reintentar" handleClick={recargar} />
                    <TextLink label="Ir al inicio" handleClick={irAlInicio} />
                </View>
            </Screen>
        );
    }

    return (
        <Screen>
            <FormScroll>
                <View style={styles.encabezado}>
                    <Ionicons name="checkmark-circle" size={64} color={theme.colors.success} />
                    <Text style={styles.titulo}>¡Sesión completada!</Text>
                    <Text style={styles.subtitulo}>{sesion.rutina_nombre}</Text>
                </View>

                <Card title="Tu sesión">
                    <Dato etiqueta="Fecha" valor={formatearDiaYMes(sesion.iniciada_en)} />
                    <Dato
                        etiqueta="Duración"
                        valor={
                            sesion.duracion_segundos !== null
                                ? formatearDuracion(sesion.duracion_segundos)
                                : '—'
                        }
                    />
                    <Dato etiqueta="Series" valor={String(totalSeries)} />
                    <Dato etiqueta="Volumen total" valor={formatearVolumen(volumenTotal)} />
                </Card>

                {estado === 'calificando' && (
                    <Card title="¿Cómo te fue?">
                        <View style={styles.estrellas}>
                            <Estrellas
                                value={calificacion}
                                onChange={setCalificacion}
                                disabled={guardando}
                            />
                        </View>
                        <Text style={styles.label}>Nota (opcional)</Text>
                        <TextInput
                            style={styles.nota}
                            value={nota}
                            onChangeText={setNota}
                            placeholder="¿Algo que quieras recordar de hoy?"
                            placeholderTextColor={theme.colors.textMuted}
                            multiline
                            maxLength={MAX_NOTA}
                            editable={!guardando}
                            accessibilityLabel="Nota"
                        />
                        {errorGuardar !== '' && <Text style={styles.error}>{errorGuardar}</Text>}
                        <StyledButton
                            label={guardando ? 'Guardando...' : 'Guardar calificación'}
                            handleClick={() => calificar(calificacion, nota)}
                            disabled={calificacion === 0 || guardando}
                        />
                        <TextLink label="Omitir" handleClick={omitir} disabled={guardando} />
                    </Card>
                )}

                {estado === 'guardada' && (
                    <Card title="Calificación guardada">
                        <Stars value={sesion.calificacion ?? calificacion} size={24} />
                        {sesion.nota ? <Text style={styles.textoNota}>{sesion.nota}</Text> : null}
                    </Card>
                )}

                {estado === 'omitida' && (
                    <Card title="Listo">
                        <Text style={styles.texto}>Sesión guardada sin calificación.</Text>
                    </Card>
                )}

                {estado !== 'calificando' && (
                    <StyledButton label="Ir al inicio" handleClick={irAlInicio} />
                )}
            </FormScroll>
        </Screen>
    );
};

// Una fila "etiqueta ........ valor" del resumen.
interface DatoProps {
    etiqueta: string;
    valor: string;
}

const Dato = ({ etiqueta, valor }: DatoProps) => (
    <View style={styles.dato}>
        <Text style={styles.datoEtiqueta}>{etiqueta}</Text>
        <Text style={styles.datoValor}>{valor}</Text>
    </View>
);

const styles = StyleSheet.create({
    centro: { flex: 1, justifyContent: 'center', gap: theme.spacing.md },
    encabezado: {
        alignItems: 'center',
        gap: theme.spacing.xs,
        marginBottom: theme.spacing.lg,
        marginTop: theme.spacing.md,
    },
    titulo: { color: theme.colors.text, fontSize: theme.fontSize.xl, fontWeight: 'bold' },
    subtitulo: { color: theme.colors.textMuted, fontSize: theme.fontSize.md },
    dato: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        paddingVertical: theme.spacing.xs,
    },
    datoEtiqueta: { color: theme.colors.textMuted, fontSize: theme.fontSize.md },
    datoValor: { color: theme.colors.text, fontSize: theme.fontSize.md, fontWeight: 'bold' },
    estrellas: { marginVertical: theme.spacing.md },
    label: {
        color: theme.colors.text,
        fontSize: theme.fontSize.sm,
        marginBottom: theme.spacing.xs,
    },
    // Mismo aspecto que el componente Input, pero con varias líneas.
    nota: {
        backgroundColor: theme.colors.background,
        borderColor: theme.colors.border,
        borderRadius: 12,
        borderWidth: 1,
        color: theme.colors.text,
        fontSize: theme.fontSize.md,
        marginBottom: theme.spacing.md,
        minHeight: 88,
        padding: theme.spacing.md,
        textAlignVertical: 'top',
    },
    error: {
        color: theme.colors.error,
        fontSize: theme.fontSize.sm,
        marginBottom: theme.spacing.sm,
        textAlign: 'center',
    },
    texto: { color: theme.colors.text, fontSize: theme.fontSize.md },
    textoNota: { color: theme.colors.text, fontSize: theme.fontSize.sm, marginTop: theme.spacing.xs },
});
