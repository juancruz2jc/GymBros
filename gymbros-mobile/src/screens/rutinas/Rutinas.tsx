import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useCallback, useMemo, useState } from 'react';
import { Alert, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { RutinaCard } from '../../components/RutinaCard';
import { Screen } from '../../components/Screen';
import { useRutinas } from '../../hooks/useRutinas';
import { MainStackParamList } from '../../navigation/types';
import { theme } from '../../theme/theme';
import { Rutina } from '../../types/rutina';

type NavigationProp = NativeStackNavigationProp<MainStackParamList>;

export const Rutinas = () => {
    const navigation = useNavigation<NavigationProp>();
    const [soloFavoritas, setSoloFavoritas] = useState<boolean>(false);

    const {
        rutinas,
        cargando,
        error,
        recargar,
        alternarFavorita,
        duplicar,
        eliminar,
    } = useRutinas();

    useFocusEffect(
        useCallback(() => {
            recargar();
        }, [recargar]),
    );

    const rutinasVisibles = useMemo(() => {
        if (!soloFavoritas) return rutinas;
        return rutinas.filter((r) => r.favorita);
    }, [rutinas, soloFavoritas]);

    const confirmarEliminar = (rutina: Rutina) => {
        Alert.alert(
            '¿Eliminar esta rutina?',
            `Se eliminará "${rutina.nombre}". Las sesiones que ya registraste con esta rutina se conservan en tu historial.`,
            [
                { text: 'Cancelar', style: 'cancel' },
                {
                    text: 'Eliminar',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await eliminar(rutina.id);
                        } catch {
                            Alert.alert('Error', 'No se pudo eliminar la rutina. Intenta de nuevo.');
                        }
                    },
                },
            ],
        );
    };

    const handleDuplicar = async (rutina: Rutina) => {
        try {
            await duplicar(rutina.id);
        } catch {
            Alert.alert('Error', 'No se pudo duplicar la rutina. Intenta de nuevo.');
        }
    };

    const handleToggleFavorita = async (id: string) => {
        try {
            await alternarFavorita(id);
        } catch {
            Alert.alert('Error', 'No se pudo actualizar favorita.');
        }
    };

    const irACrearRutina = () => {
        navigation.navigate('CrearRutina');
    };

    const renderSkeletons = () => (
        <View style={styles.skeletonList}>
            {[1, 2, 3].map((item) => (
                <View key={item} style={styles.skeletonCard}>
                    <View style={styles.skeletonLineMd} />
                    <View style={styles.skeletonLineSm} />
                    <View style={styles.skeletonLineLg} />
                </View>
            ))}
        </View>
    );

    return (
        <Screen>
            <View style={styles.headerRow}>
                <Text style={styles.headerTitle}>Mis rutinas</Text>
                <Pressable
                    style={styles.catalogButton}
                    onPress={() => navigation.navigate('CatalogoEjercicios')}
                >
                    <Ionicons name="barbell-outline" size={16} color={theme.colors.primary} />
                    <Text style={styles.catalogButtonText}>Catálogo</Text>
                </Pressable>
            </View>

            {(rutinas.length > 0 || cargando) && (
                <View style={styles.filterBar}>
                    <Pressable
                        style={[
                            styles.favFilterPill,
                            soloFavoritas && styles.favFilterPillActive,
                        ]}
                        onPress={() => setSoloFavoritas((prev) => !prev)}
                    >
                        <Ionicons
                            name={soloFavoritas ? 'star' : 'star-outline'}
                            size={14}
                            color={soloFavoritas ? '#FFFFFF' : theme.colors.text}
                        />
                        <Text
                            style={[
                                styles.favFilterText,
                                soloFavoritas && styles.favFilterTextActive,
                            ]}
                        >
                            Solo favoritas
                        </Text>
                    </Pressable>

                    {!cargando && (
                        <Text style={styles.countText}>
                            {rutinasVisibles.length}{' '}
                            {rutinasVisibles.length === 1 ? 'rutina' : 'rutinas'}
                        </Text>
                    )}
                </View>
            )}

            {cargando ? (
                renderSkeletons()
            ) : error !== '' ? (
                <View style={styles.centerState}>
                    <View style={styles.darkCircleIcon}>
                        <Ionicons name="wifi-outline" size={32} color={theme.colors.primary} />
                    </View>
                    <Text style={styles.stateTitle}>Error de conexión</Text>
                    <Text style={styles.stateSubtitle}>{error}</Text>
                    <Pressable style={styles.primaryPillButton} onPress={recargar}>
                        <Text style={styles.primaryPillButtonText}>Reintentar</Text>
                    </Pressable>
                </View>
            ) : rutinas.length === 0 ? (
                <View style={styles.centerState}>
                    <View style={styles.darkCircleIcon}>
                        <Ionicons name="albums-outline" size={32} color={theme.colors.primary} />
                    </View>
                    <Text style={styles.stateTitle}>Aún no tienes rutinas</Text>
                    <Text style={styles.stateSubtitle}>
                        Crea tu primera rutina eligiendo ejercicios del catálogo de GymBros
                    </Text>
                    <Pressable style={styles.primaryPillButton} onPress={irACrearRutina}>
                        <Text style={styles.primaryPillButtonText}>+ Crear nueva rutina</Text>
                    </Pressable>
                </View>
            ) : (
                <>
                    <FlatList
                        data={rutinasVisibles}
                        keyExtractor={(item) => item.id}
                        renderItem={({ item }) => (
                            <RutinaCard
                                rutina={item}
                                onPress={(r) =>
                                    navigation.navigate('DetalleRutina', { rutinaId: r.id })
                                }
                                onToggleFavorita={handleToggleFavorita}
                                onEditar={(r) =>
                                    navigation.navigate('CrearRutina', { rutinaId: r.id })
                                }
                                onDuplicar={handleDuplicar}
                                onEliminar={confirmarEliminar}
                            />
                        )}
                        contentContainerStyle={
                            rutinasVisibles.length === 0
                                ? styles.emptyFilterContainer
                                : styles.listContent
                        }
                        showsVerticalScrollIndicator={false}
                        ListEmptyComponent={
                            <View style={styles.centerState}>
                                <Text style={styles.stateTitle}>Sin rutinas favoritas</Text>
                                <Text style={styles.stateSubtitle}>
                                    Toca la estrella en cualquiera de tus rutinas para marcarla
                                    como favorita.
                                </Text>
                            </View>
                        }
                    />

                    <View style={styles.footer}>
                        <Pressable style={styles.createFooterButton} onPress={irACrearRutina}>
                            <Text style={styles.createFooterButtonText}>+ Crear nueva rutina</Text>
                        </Pressable>
                    </View>
                </>
            )}
        </Screen>
    );
};

const styles = StyleSheet.create({
    headerRow: {
        alignItems: 'center',
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: theme.spacing.md,
    },
    headerTitle: {
        color: theme.colors.text,
        fontSize: theme.fontSize.xl,
        fontWeight: 'bold',
    },
    catalogButton: {
        alignItems: 'center',
        backgroundColor: theme.colors.primarySoft,
        borderColor: theme.colors.border,
        borderRadius: 20,
        borderWidth: 1,
        flexDirection: 'row',
        gap: 6,
        paddingHorizontal: 12,
        paddingVertical: 6,
    },
    catalogButtonText: {
        color: theme.colors.primaryText,
        fontSize: theme.fontSize.sm,
        fontWeight: 'bold',
    },
    filterBar: {
        alignItems: 'center',
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: theme.spacing.md,
    },
    favFilterPill: {
        alignItems: 'center',
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 20,
        borderWidth: 1,
        flexDirection: 'row',
        gap: 6,
        paddingHorizontal: 14,
        paddingVertical: 6,
    },
    favFilterPillActive: {
        backgroundColor: '#1E1B18',
        borderColor: '#1E1B18',
    },
    favFilterText: {
        color: theme.colors.text,
        fontSize: theme.fontSize.sm,
        fontWeight: '600',
    },
    favFilterTextActive: {
        color: '#FFFFFF',
    },
    countText: {
        color: theme.colors.textMuted,
        fontSize: theme.fontSize.sm,
    },
    listContent: {
        paddingBottom: theme.spacing.md,
    },
    emptyFilterContainer: {
        flexGrow: 1,
        justifyContent: 'center',
    },
    centerState: {
        alignItems: 'center',
        flex: 1,
        gap: theme.spacing.md,
        justifyContent: 'center',
        paddingHorizontal: theme.spacing.lg,
    },
    darkCircleIcon: {
        alignItems: 'center',
        backgroundColor: '#1E1B18',
        borderRadius: 36,
        height: 72,
        justifyContent: 'center',
        width: 72,
    },
    stateTitle: {
        color: theme.colors.text,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
    },
    stateSubtitle: {
        color: theme.colors.textMuted,
        fontSize: theme.fontSize.sm,
        lineHeight: 20,
        textAlign: 'center',
    },
    primaryPillButton: {
        backgroundColor: theme.colors.primary,
        borderRadius: 24,
        paddingHorizontal: 28,
        paddingVertical: 12,
    },
    primaryPillButtonText: {
        color: '#FFFFFF',
        fontSize: theme.fontSize.md,
        fontWeight: 'bold',
    },
    footer: {
        paddingTop: theme.spacing.xs,
    },
    createFooterButton: {
        alignItems: 'center',
        backgroundColor: theme.colors.primary,
        borderRadius: 24,
        paddingVertical: 14,
    },
    createFooterButtonText: {
        color: '#FFFFFF',
        fontSize: theme.fontSize.md,
        fontWeight: 'bold',
    },
    skeletonList: {
        gap: theme.spacing.md,
    },
    skeletonCard: {
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 16,
        borderWidth: 1,
        gap: 10,
        padding: theme.spacing.md,
    },
    skeletonLineMd: {
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 6,
        height: 14,
        width: '55%',
    },
    skeletonLineSm: {
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 6,
        height: 10,
        width: '40%',
    },
    skeletonLineLg: {
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 8,
        height: 22,
        width: '85%',
    },
});