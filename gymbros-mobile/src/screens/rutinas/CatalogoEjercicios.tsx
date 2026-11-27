import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useMemo, useState } from 'react';
import {
    FlatList,
    Pressable,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    View,
} from 'react-native';
import { ChipOption, Chips } from '../../components/Chips';
import { EjercicioItem } from '../../components/EjercicioItem';
import { Screen } from '../../components/Screen';
import { useEjercicios } from '../../hooks/useEjercicios';
import { MainStackParamList } from '../../navigation/types';
import { theme } from '../../theme/theme';
import { Ejercicio } from '../../types/ejercicio';

const OPCIONES_GRUPO: ChipOption[] = [
    { value: 'pecho', label: 'Pecho' },
    { value: 'espalda', label: 'Espalda' },
    { value: 'piernas', label: 'Piernas' },
    { value: 'hombros', label: 'Hombros' },
    { value: 'brazos', label: 'Brazos' },
    { value: 'abdomen', label: 'Abdomen' },
];

const OPCIONES_EQUIPO: ChipOption[] = [
    { value: 'barra', label: 'Barra' },
    { value: 'mancuernas', label: 'Mancuernas' },
    { value: 'maquina', label: 'Máquina' },
    { value: 'polea', label: 'Polea' },
    { value: 'peso_corporal', label: 'Peso corporal' },
];

const OPCIONES_CATEGORIA: ChipOption[] = [
    { value: 'fuerza', label: 'Fuerza' },
    { value: 'hipertrofia', label: 'Hipertrofia' },
    { value: 'cardio', label: 'Cardio' },
    { value: 'estiramiento', label: 'Estiramiento' },
];

type FiltroAbierto = 'grupo' | 'equipo' | 'categoria' | null;

interface Props {
    onSelectEjercicio?: (ejercicio: Ejercicio) => void;
}

export const CatalogoEjercicios = ({ onSelectEjercicio }: Props) => {
    const navigation = useNavigation<NativeStackNavigationProp<MainStackParamList>>();
    const [busqueda, setBusqueda] = useState<string>('');
    const [grupoMuscular, setGrupoMuscular] = useState<string | null>(null);
    const [equipo, setEquipo] = useState<string | null>(null);
    const [categoria, setCategoria] = useState<string | null>(null);
    const [filtroAbierto, setFiltroAbierto] = useState<FiltroAbierto>(null);

    const { ejercicios, cargando, error, filtrar, recargar } = useEjercicios();

    const aplicarFiltros = (
        nuevoGrupo: string | null,
        nuevoEquipo: string | null,
        nuevaCategoria: string | null,
    ) => {
        filtrar({
            grupo_muscular: nuevoGrupo ?? undefined,
            equipo: nuevoEquipo ?? undefined,
            categoria: nuevaCategoria ?? undefined,
        });
    };

    const ejerciciosFiltrados = useMemo(() => {
        const termino = busqueda.trim().toLowerCase();
        if (!termino) return ejercicios;
        return ejercicios.filter((ej) => ej.nombre_es.toLowerCase().includes(termino));
    }, [ejercicios, busqueda]);

    const limpiarFiltros = () => {
        setBusqueda('');
        setGrupoMuscular(null);
        setEquipo(null);
        setCategoria(null);
        setFiltroAbierto(null);
        filtrar({});
    };

    const toggleDropdown = (key: FiltroAbierto) => {
        setFiltroAbierto((prev) => (prev === key ? null : key));
    };

    const renderSkeletons = () => (
        <View style={styles.skeletonList}>
            {[1, 2, 3, 4, 5].map((item) => (
                <View key={item} style={styles.skeletonCard}>
                    <View style={styles.skeletonThumb} />
                    <View style={styles.skeletonLines}>
                        <View style={styles.skeletonLineLg} />
                        <View style={styles.skeletonLineSm} />
                    </View>
                </View>
            ))}
        </View>
    );

    return (
        <Screen>
            <Text style={styles.headerTitle}>Catálogo de ejercicios</Text>

            {/* Barra de búsqueda */}
            <View style={styles.searchBar}>
                <Ionicons name="search-outline" size={18} color={theme.colors.textMuted} />
                <TextInput
                    style={styles.searchInput}
                    placeholder="Buscar ejercicio..."
                    placeholderTextColor={theme.colors.textMuted}
                    value={busqueda}
                    onChangeText={setBusqueda}
                />
                {busqueda.length > 0 && (
                    <Pressable onPress={() => setBusqueda('')}>
                        <Ionicons name="close-circle" size={18} color={theme.colors.textMuted} />
                    </Pressable>
                )}
            </View>

            {/* Fila horizontal de chips desplegables */}
            <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                style={styles.dropdownRow}
                contentContainerStyle={styles.dropdownRowContent}
            >
                <Pressable
                    style={[
                        styles.dropdownPill,
                        (grupoMuscular || filtroAbierto === 'grupo') && styles.dropdownPillActive,
                    ]}
                    onPress={() => toggleDropdown('grupo')}
                >
                    <Text
                        style={[
                            styles.dropdownPillText,
                            (grupoMuscular || filtroAbierto === 'grupo') &&
                            styles.dropdownPillTextActive,
                        ]}
                    >
                        {grupoMuscular
                            ? OPCIONES_GRUPO.find((o) => o.value === grupoMuscular)?.label
                            : 'Grupo muscular'}
                    </Text>
                    <Ionicons
                        name={filtroAbierto === 'grupo' ? 'chevron-up' : 'chevron-down'}
                        size={14}
                        color={
                            grupoMuscular || filtroAbierto === 'grupo'
                                ? '#FFFFFF'
                                : theme.colors.text
                        }
                    />
                </Pressable>

                <Pressable
                    style={[
                        styles.dropdownPill,
                        (equipo || filtroAbierto === 'equipo') && styles.dropdownPillActive,
                    ]}
                    onPress={() => toggleDropdown('equipo')}
                >
                    <Text
                        style={[
                            styles.dropdownPillText,
                            (equipo || filtroAbierto === 'equipo') && styles.dropdownPillTextActive,
                        ]}
                    >
                        {equipo
                            ? OPCIONES_EQUIPO.find((o) => o.value === equipo)?.label
                            : 'Equipo'}
                    </Text>
                    <Ionicons
                        name={filtroAbierto === 'equipo' ? 'chevron-up' : 'chevron-down'}
                        size={14}
                        color={equipo || filtroAbierto === 'equipo' ? '#FFFFFF' : theme.colors.text}
                    />
                </Pressable>

                <Pressable
                    style={[
                        styles.dropdownPill,
                        (categoria || filtroAbierto === 'categoria') && styles.dropdownPillActive,
                    ]}
                    onPress={() => toggleDropdown('categoria')}
                >
                    <Text
                        style={[
                            styles.dropdownPillText,
                            (categoria || filtroAbierto === 'categoria') &&
                            styles.dropdownPillTextActive,
                        ]}
                    >
                        {categoria
                            ? OPCIONES_CATEGORIA.find((o) => o.value === categoria)?.label
                            : 'Categoría'}
                    </Text>
                    <Ionicons
                        name={filtroAbierto === 'categoria' ? 'chevron-up' : 'chevron-down'}
                        size={14}
                        color={
                            categoria || filtroAbierto === 'categoria'
                                ? '#FFFFFF'
                                : theme.colors.text
                        }
                    />
                </Pressable>
            </ScrollView>

            {/* Desplegable activo */}
            {filtroAbierto === 'grupo' && (
                <View style={styles.popoverBox}>
                    <Chips
                        options={OPCIONES_GRUPO}
                        selected={grupoMuscular}
                        handleChange={(val) => {
                            const next = val === grupoMuscular ? null : val;
                            setGrupoMuscular(next);
                            aplicarFiltros(next, equipo, categoria);
                        }}
                    />
                </View>
            )}
            {filtroAbierto === 'equipo' && (
                <View style={styles.popoverBox}>
                    <Chips
                        options={OPCIONES_EQUIPO}
                        selected={equipo}
                        handleChange={(val) => {
                            const next = val === equipo ? null : val;
                            setEquipo(next);
                            aplicarFiltros(grupoMuscular, next, categoria);
                        }}
                    />
                </View>
            )}
            {filtroAbierto === 'categoria' && (
                <View style={styles.popoverBox}>
                    <Chips
                        options={OPCIONES_CATEGORIA}
                        selected={categoria}
                        handleChange={(val) => {
                            const next = val === categoria ? null : val;
                            setCategoria(next);
                            aplicarFiltros(grupoMuscular, equipo, next);
                        }}
                    />
                </View>
            )}

            {/* Contenido por estado */}
            {cargando ? (
                renderSkeletons()
            ) : error !== '' ? (
                <View style={styles.centerState}>
                    <View style={styles.darkCircleIcon}>
                        <Ionicons name="wifi-outline" size={32} color={theme.colors.primary} />
                    </View>
                    <Text style={styles.stateTitle}>Sin conexión</Text>
                    <Text style={styles.stateSubtitle}>
                        No pudimos cargar el catálogo. Revisa tu conexión a internet e intenta de
                        nuevo.
                    </Text>
                    <Pressable style={styles.primaryPillButton} onPress={recargar}>
                        <Text style={styles.primaryPillButtonText}>Reintentar</Text>
                    </Pressable>
                </View>
            ) : (
                <FlatList
                    data={ejerciciosFiltrados}
                    keyExtractor={(item) => item.id}
                    renderItem={({ item }) => (
                        <EjercicioItem
                            ejercicio={item}
                            onSelect={onSelectEjercicio}
                            onPress={(ej) =>
                                navigation.navigate('DetalleEjercicio', { ejercicio: ej })
                            }
                        />
                    )}
                    contentContainerStyle={
                        ejerciciosFiltrados.length === 0 ? styles.emptyContainer : styles.listContent
                    }
                    showsVerticalScrollIndicator={false}
                    ListEmptyComponent={
                        <View style={styles.centerState}>
                            <View style={styles.darkCircleIcon}>
                                <Ionicons name="search" size={30} color={theme.colors.primary} />
                            </View>
                            <Text style={styles.stateTitle}>Sin resultados</Text>
                            <Text style={styles.stateSubtitle}>
                                {busqueda.trim()
                                    ? `No encontramos ejercicios para "${busqueda.trim()}" con estos filtros. Prueba con otro nombre o ajusta los filtros.`
                                    : 'No encontramos ejercicios con estos filtros. Prueba ajustando las opciones.'}
                            </Text>
                            <Pressable style={styles.outlineButton} onPress={limpiarFiltros}>
                                <Text style={styles.outlineButtonText}>Limpiar filtros</Text>
                            </Pressable>
                        </View>
                    }
                />
            )}
        </Screen>
    );
};

const styles = StyleSheet.create({
    headerTitle: {
        color: theme.colors.text,
        fontSize: theme.fontSize.xl,
        fontWeight: 'bold',
        marginBottom: theme.spacing.md,
    },
    searchBar: {
        alignItems: 'center',
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 24,
        borderWidth: 1,
        flexDirection: 'row',
        gap: theme.spacing.sm,
        marginBottom: theme.spacing.sm,
        paddingHorizontal: theme.spacing.md,
        paddingVertical: 10,
    },
    searchInput: {
        color: theme.colors.text,
        flex: 1,
        fontSize: theme.fontSize.md,
    },
    dropdownRow: {
        flexGrow: 0,
        flexShrink: 0,
        marginBottom: theme.spacing.md,
        minHeight: 42,
    },
    dropdownRowContent: {
        alignItems: 'center',
        gap: theme.spacing.sm,
        paddingVertical: 2,
    },
    dropdownPill: {
        alignItems: 'center',
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 20,
        borderWidth: 1,
        flexDirection: 'row',
        gap: 6,
        height: 38,
        justifyContent: 'center',
        paddingHorizontal: 14,
    },
    dropdownPillActive: {
        backgroundColor: '#1E1B18',
        borderColor: '#1E1B18',
    },
    dropdownPillText: {
        color: theme.colors.text,
        fontSize: theme.fontSize.sm,
        fontWeight: '600',
        includeFontPadding: false,
    },
    dropdownPillTextActive: {
        color: '#FFFFFF',
    },
    popoverBox: {
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 16,
        borderWidth: 1,
        marginBottom: theme.spacing.md,
        padding: theme.spacing.sm,
    },
    listContent: {
        paddingBottom: theme.spacing.xl,
    },
    emptyContainer: {
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
    outlineButton: {
        borderColor: theme.colors.border,
        borderRadius: 20,
        borderWidth: 1,
        paddingHorizontal: 24,
        paddingVertical: 10,
    },
    outlineButtonText: {
        color: theme.colors.text,
        fontSize: theme.fontSize.sm,
        fontWeight: '600',
    },
    primaryPillButton: {
        backgroundColor: theme.colors.primary,
        borderRadius: 24,
        paddingHorizontal: 32,
        paddingVertical: 12,
    },
    primaryPillButtonText: {
        color: '#FFFFFF',
        fontSize: theme.fontSize.md,
        fontWeight: 'bold',
    },
    skeletonList: {
        gap: theme.spacing.sm,
    },
    skeletonCard: {
        alignItems: 'center',
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 16,
        borderWidth: 1,
        flexDirection: 'row',
        gap: theme.spacing.md,
        padding: theme.spacing.sm,
    },
    skeletonThumb: {
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 12,
        height: 56,
        width: 56,
    },
    skeletonLines: {
        flex: 1,
        gap: 8,
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