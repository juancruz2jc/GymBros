import { useNavigation } from '@react-navigation/native';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { EmptyState } from '../../components/EmptyState';
import { Loading } from '../../components/Loading';
import { Screen } from '../../components/Screen';
import { TarjetaSesion } from '../../components/TarjetaSesion';
import { useHistorial } from '../../hooks/useHistorial';
import { theme } from '../../theme/theme';

// Historial: entrenamientos finalizados, del más reciente al más antiguo
// (GYM-195).
export const Historial = () => {
    const navigation = useNavigation();
    const {
        sesiones,
        cargando,
        refrescando,
        cargandoMas,
        error,
        recargar,
        refrescar,
        cargarMas,
    } = useHistorial();

    if (cargando) {
        return (
            <Screen>
                <Loading />
            </Screen>
        );
    }

    // Sin nada que mostrar y con error: solo el error y reintentar.
    if (error !== '' && sesiones.length === 0) {
        return (
            <Screen>
                <EmptyState message={error} actionLabel="Reintentar" onAction={recargar} />
            </Screen>
        );
    }

    return (
        <Screen>
            {/* Con datos en pantalla, un error (p. ej. al cargar más) va arriba. */}
            {error !== '' && <Text style={styles.error}>{error}</Text>}
            <FlatList
                data={sesiones}
                keyExtractor={(sesion) => sesion.id}
                renderItem={({ item }) => <TarjetaSesion sesion={item} />}
                contentContainerStyle={sesiones.length === 0 && styles.vacia}
                onEndReached={cargarMas}
                onEndReachedThreshold={0.5}
                refreshControl={
                    <RefreshControl
                        refreshing={refrescando}
                        onRefresh={refrescar}
                        colors={[theme.colors.primary]}
                        tintColor={theme.colors.primary}
                    />
                }
                ListEmptyComponent={
                    <EmptyState
                        message="Aún no has entrenado. Tus entrenamientos finalizados aparecerán aquí."
                        actionLabel="Ver mis rutinas"
                        onAction={() => navigation.navigate('Tabs', { screen: 'Rutinas' })}
                    />
                }
                ListFooterComponent={
                    cargandoMas ? (
                        <View style={styles.pie}>
                            <ActivityIndicator color={theme.colors.primary} />
                        </View>
                    ) : undefined
                }
            />
        </Screen>
    );
};

const styles = StyleSheet.create({
    vacia: { flexGrow: 1 },
    error: {
        color: theme.colors.error,
        fontSize: theme.fontSize.sm,
        marginBottom: theme.spacing.sm,
        textAlign: 'center',
    },
    pie: { paddingVertical: theme.spacing.md },
});
