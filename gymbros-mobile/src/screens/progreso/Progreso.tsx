import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { useCallback, useState } from 'react';
import { Alert, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { EmptyState } from '../../components/EmptyState';
import { FAB } from '../../components/FAB';
import { Loading } from '../../components/Loading';
import { Screen } from '../../components/Screen';
import { useMediciones } from '../../hooks/useMediciones';
import { getErrorMessage } from '../../services/api';
import { theme } from '../../theme/theme';
import { CategoriaImc, Medicion } from '../../types/medicion';
import { formatearFecha } from '../../utils/formato';

// Texto y color de cada categoría de IMC.
const CATEGORIAS: Record<CategoriaImc, { texto: string; color: string }> = {
    bajo_peso: { texto: 'Bajo peso', color: theme.colors.primary },
    normal: { texto: 'Normal', color: theme.colors.success },
    sobrepeso: { texto: 'Sobrepeso', color: theme.colors.primary },
    obesidad: { texto: 'Obesidad', color: theme.colors.error },
};

// Texto y color de la categoría que manda la API, o null si no hay IMC.
const obtenerCategoria = (categoria: string | null) =>
    categoria !== null && categoria in CATEGORIAS ? CATEGORIAS[categoria as CategoriaImc] : null;

// EstadoActual: tarjeta "Tu estado actual" con la última medición.
interface EstadoActualProps {
    medicion: Medicion;
}

const EstadoActual = ({ medicion }: EstadoActualProps) => {
    const categoria = obtenerCategoria(medicion.categoria_imc);

    return (
        <View style={styles.tarjeta}>
            <Text style={styles.titulo}>Tu estado actual</Text>
            {/* Text anidado: la etiqueta normal y el valor resaltado. */}
            <Text style={styles.linea}>
                Peso: <Text style={styles.valor}>{medicion.peso_kg} kg</Text>
            </Text>
            {medicion.imc !== null ? (
                <Text style={styles.linea}>
                    IMC: <Text style={styles.valor}>{medicion.imc}</Text>
                    {categoria && (
                        <Text style={[styles.valor, { color: categoria.color }]}>
                            {' '}· {categoria.texto}
                        </Text>
                    )}
                </Text>
            ) : (
                <Text style={styles.aviso}>Agrega tu altura en Perfil para calcular tu IMC</Text>
            )}
            <Text style={styles.textoSuave}>{formatearFecha(medicion.fecha)}</Text>
        </View>
    );
};

// FilaMedicion: una medición del historial. Mantener presionado la elimina.
interface FilaProps {
    medicion: Medicion;
    onLongPress?: () => void;
}

const FilaMedicion = ({ medicion, onLongPress }: FilaProps) => {
    const categoria = obtenerCategoria(medicion.categoria_imc);

    return (
        <Pressable
            style={({ pressed }) => [styles.fila, pressed && styles.presionada]}
            onLongPress={onLongPress}
        >
            <View>
                <Text style={styles.textoSuave}>{formatearFecha(medicion.fecha)}</Text>
                <Text style={styles.peso}>{medicion.peso_kg} kg</Text>
            </View>
            <View style={styles.derecha}>
                <Text style={styles.linea}>IMC {medicion.imc ?? '—'}</Text>
                {categoria && (
                    <Text style={[styles.categoria, { color: categoria.color }]}>
                        {categoria.texto}
                    </Text>
                )}
            </View>
        </Pressable>
    );
};

// Progreso: estado actual del usuario y su historial de mediciones.
export const Progreso = () => {
    const navigation = useNavigation();
    const { mediciones, ultima, cargando, error, recargar, eliminar } = useMediciones();
    const [refrescando, setRefrescando] = useState(false);

    // Se recarga cada vez que la pestaña se muestra, por ejemplo al volver de
    // registrar una medición.
    useFocusEffect(
        useCallback(() => {
            recargar();
        }, [recargar]),
    );

    const refrescar = async () => {
        setRefrescando(true);
        await recargar();
        setRefrescando(false);
    };

    const irARegistrar = () => navigation.navigate('RegistrarMedicion');

    const confirmarEliminar = (medicion: Medicion) => {
        Alert.alert(
            'Eliminar medición',
            `¿Eliminar la medición del ${formatearFecha(medicion.fecha)}? No se puede deshacer.`,
            [
                { text: 'Cancelar', style: 'cancel' },
                {
                    text: 'Eliminar',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await eliminar(medicion.id);
                        } catch (e) {
                            Alert.alert('No se pudo eliminar', getErrorMessage(e));
                        }
                    },
                },
            ],
        );
    };

    if (cargando) {
        return <Loading />;
    }

    if (!ultima) {
        return (
            <Screen>
                {error !== '' ? (
                    <EmptyState message={error} actionLabel="Reintentar" onAction={refrescar} />
                ) : (
                    <EmptyState
                        message="Aún no tienes mediciones. Registra la primera para ver tu progreso."
                        actionLabel="Nueva medición"
                        onAction={irARegistrar}
                    />
                )}
            </Screen>
        );
    }

    return (
        <Screen>
            <EstadoActual medicion={ultima} />

            {error !== '' && <Text style={styles.error}>{error}</Text>}

            <Text style={styles.subtitulo}>Historial</Text>
            <Text style={styles.textoSuave}>Mantén presionada una medición para eliminarla.</Text>

            <FlatList
                data={mediciones}
                keyExtractor={(medicion) => medicion.id}
                renderItem={({ item }) => (
                    <FilaMedicion medicion={item} onLongPress={() => confirmarEliminar(item)} />
                )}
                contentContainerStyle={styles.lista}
                refreshControl={<RefreshControl refreshing={refrescando} onRefresh={refrescar} />}
            />

            <FAB label="Nueva medición" onPress={irARegistrar} />
        </Screen>
    );
};

const styles = StyleSheet.create({
    tarjeta: {
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 12,
        borderWidth: 1,
        gap: theme.spacing.xs,
        marginBottom: theme.spacing.md,
        padding: theme.spacing.md,
    },
    titulo: { color: theme.colors.text, fontSize: theme.fontSize.lg, fontWeight: 'bold' },
    subtitulo: { color: theme.colors.text, fontSize: theme.fontSize.lg, fontWeight: 'bold' },
    linea: { color: theme.colors.text, fontSize: theme.fontSize.md },
    valor: { color: theme.colors.primary, fontWeight: 'bold' },
    aviso: { color: theme.colors.error, fontSize: theme.fontSize.md },
    textoSuave: { color: theme.colors.textMuted, fontSize: theme.fontSize.sm },
    error: {
        color: theme.colors.error,
        fontSize: theme.fontSize.sm,
        marginBottom: theme.spacing.sm,
    },
    // Espacio abajo para que el FAB no tape la última fila.
    lista: { gap: theme.spacing.sm, paddingTop: theme.spacing.sm, paddingBottom: theme.spacing.xl * 2 },
    fila: {
        alignItems: 'center',
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 12,
        borderWidth: 1,
        flexDirection: 'row',
        justifyContent: 'space-between',
        padding: theme.spacing.md,
    },
    presionada: { opacity: 0.7 },
    peso: { color: theme.colors.text, fontSize: theme.fontSize.lg, fontWeight: 'bold' },
    derecha: { alignItems: 'flex-end' },
    categoria: { fontSize: theme.fontSize.sm, fontWeight: 'bold' },
});
