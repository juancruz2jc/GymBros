import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { useCallback, useState } from 'react';
import { Alert, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { EmptyState } from '../../components/EmptyState';
import { FAB } from '../../components/FAB';
import { Loading } from '../../components/Loading';
import { Screen } from '../../components/Screen';
import { obtenerCategoria, TarjetaMedicion } from '../../components/TarjetaMedicion';
import { useMediciones } from '../../hooks/useMediciones';
import { getErrorMessage } from '../../services/api';
import { theme } from '../../theme/theme';
import { Medicion } from '../../types/medicion';
import { formatearFecha } from '../../utils/formato';

// FilaMedicion: una medición del historial. Tocarla la edita y mantenerla
// presionada la elimina.
interface FilaProps {
    medicion: Medicion;
    onPress?: () => void;
    onLongPress?: () => void;
}

const FilaMedicion = ({ medicion, onPress, onLongPress }: FilaProps) => {
    const categoria = obtenerCategoria(medicion.categoria_imc);

    return (
        <Pressable
            style={({ pressed }) => [styles.fila, pressed && styles.presionada]}
            onPress={onPress}
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
            <TarjetaMedicion medicion={ultima} />

            {error !== '' && <Text style={styles.error}>{error}</Text>}

            <View style={styles.encabezado}>
                <Text style={styles.subtitulo}>Historial</Text>
                {/* Comparar necesita al menos dos mediciones. */}
                {mediciones.length >= 2 && (
                    <Pressable onPress={() => navigation.navigate('CompararMediciones')}>
                        <Text style={styles.enlace}>Comparar</Text>
                    </Pressable>
                )}
            </View>
            <Text style={styles.textoSuave}>Toca una medición para editarla o mantenla presionada para eliminarla.</Text>

            <FlatList
                data={mediciones}
                keyExtractor={(medicion) => medicion.id}
                renderItem={({ item }) => (
                    <FilaMedicion
                        medicion={item}
                        onPress={() =>
                            navigation.navigate('RegistrarMedicion', { medicionId: item.id })
                        }
                        onLongPress={() => confirmarEliminar(item)}
                    />
                )}
                contentContainerStyle={styles.lista}
                refreshControl={<RefreshControl refreshing={refrescando} onRefresh={refrescar} />}
            />

            <FAB label="Nueva medición" onPress={irARegistrar} />
        </Screen>
    );
};

const styles = StyleSheet.create({
    encabezado: {
        alignItems: 'center',
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    enlace: { color: theme.colors.primary, fontSize: theme.fontSize.md, fontWeight: 'bold' },
    subtitulo: { color: theme.colors.text, fontSize: theme.fontSize.lg, fontWeight: 'bold' },
    linea: { color: theme.colors.text, fontSize: theme.fontSize.md },
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
