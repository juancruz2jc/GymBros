import { Ionicons } from '@expo/vector-icons';
import { RouteProp, useNavigation, useRoute } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { MainStackParamList } from '../../navigation/types';
import { theme } from '../../theme/theme';

type DetalleRouteProp = RouteProp<MainStackParamList, 'DetalleEjercicio'>;

export const DetalleEjercicio = () => {
    const navigation = useNavigation<NativeStackNavigationProp<MainStackParamList>>();
    const { params } = useRoute<DetalleRouteProp>();
    const { ejercicio } = params;

    return (
        <Screen>
            <Pressable style={styles.backButton} onPress={() => navigation.goBack()}>
                <Ionicons name="chevron-back" size={24} color={theme.colors.text} />
            </Pressable>

            <View style={styles.mediaBox}>
                {ejercicio.gif_url ? (
                    <>
                        <Image
                            source={{ uri: ejercicio.gif_url }}
                            style={styles.gifImage}
                            resizeMode="cover"
                        />
                        <View style={styles.gifBadge}>
                            <Text style={styles.gifBadgeText}>Gif</Text>
                        </View>
                    </>
                ) : (
                    <View style={styles.noGifContainer}>
                        <Ionicons name="image-outline" size={40} color={theme.colors.primary} />
                        <Text style={styles.noGifText}>Gif no disponible</Text>
                    </View>
                )}
            </View>

            <Text style={styles.title}>{ejercicio.nombre_es}</Text>

            <View style={styles.pillsRow}>
                <View style={styles.pillPrimary}>
                    <Text style={styles.pillPrimaryText}>{ejercicio.grupo_muscular}</Text>
                </View>
                <View style={styles.pillDark}>
                    <Text style={styles.pillDarkText}>{ejercicio.equipo}</Text>
                </View>
                <View style={styles.pillLight}>
                    <Text style={styles.pillLightText}>{ejercicio.categoria}</Text>
                </View>
            </View>

            <View style={styles.footer}>
                <Pressable
                    style={styles.ctaButton}
                    onPress={() => {
                        // Aquí conectaremos con CrearRutina / AgregarARutina en la siguiente pantalla
                        navigation.goBack();
                    }}
                >
                    <Text style={styles.ctaButtonText}>Agregar a rutina</Text>
                </Pressable>
            </View>
        </Screen>
    );
};

const styles = StyleSheet.create({
    backButton: {
        alignSelf: 'flex-start',
        marginBottom: theme.spacing.md,
        padding: 4,
    },
    mediaBox: {
        backgroundColor: theme.colors.primarySoft,
        borderRadius: 20,
        height: 280,
        marginBottom: theme.spacing.lg,
        overflow: 'hidden',
        position: 'relative',
        width: '100%',
    },
    gifImage: {
        height: '100%',
        width: '100%',
    },
    gifBadge: {
        backgroundColor: '#1E1B18',
        borderRadius: 8,
        paddingHorizontal: 10,
        paddingVertical: 4,
        position: 'absolute',
        right: 12,
        top: 12,
    },
    gifBadgeText: {
        color: '#FFFFFF',
        fontSize: 12,
        fontWeight: 'bold',
    },
    noGifContainer: {
        alignItems: 'center',
        flex: 1,
        gap: theme.spacing.sm,
        justifyContent: 'center',
    },
    noGifText: {
        color: theme.colors.text,
        fontSize: theme.fontSize.sm,
        fontWeight: '600',
    },
    title: {
        color: theme.colors.text,
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: theme.spacing.md,
    },
    pillsRow: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: theme.spacing.sm,
    },
    pillPrimary: {
        backgroundColor: theme.colors.primary,
        borderRadius: 16,
        paddingHorizontal: 14,
        paddingVertical: 6,
    },
    pillPrimaryText: {
        color: '#FFFFFF',
        fontSize: 12,
        fontWeight: 'bold',
        textTransform: 'capitalize',
    },
    pillDark: {
        backgroundColor: '#1E1B18',
        borderRadius: 16,
        paddingHorizontal: 14,
        paddingVertical: 6,
    },
    pillDarkText: {
        color: '#FFFFFF',
        fontSize: 12,
        fontWeight: 'bold',
        textTransform: 'capitalize',
    },
    pillLight: {
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 16,
        borderWidth: 1,
        paddingHorizontal: 14,
        paddingVertical: 6,
    },
    pillLightText: {
        color: theme.colors.text,
        fontSize: 12,
        fontWeight: '600',
        textTransform: 'capitalize',
    },
    footer: {
        flex: 1,
        justifyContent: 'flex-end',
        paddingBottom: theme.spacing.md,
    },
    ctaButton: {
        alignItems: 'center',
        backgroundColor: theme.colors.primary,
        borderRadius: 24,
        paddingVertical: 14,
    },
    ctaButtonText: {
        color: '#FFFFFF',
        fontSize: theme.fontSize.md,
        fontWeight: 'bold',
    },
});