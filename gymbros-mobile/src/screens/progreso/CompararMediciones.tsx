import { useEffect, useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { EmptyState } from '../../components/EmptyState';
import { Loading } from '../../components/Loading';
import { Screen } from '../../components/Screen';
import { StyledButton } from '../../components/StyledButton';
import { TarjetaMedicion } from '../../components/TarjetaMedicion';
import { useMediciones } from '../../hooks/useMediciones';
import { getErrorMessage } from '../../services/api';
import { compararMediciones } from '../../services/medicionService';
import { theme } from '../../theme/theme';
import { DiferenciasMedicion, Medicion, MedicionComparativa } from '../../types/medicion';
import { formatearFecha } from '../../utils/formato';

// Cada dato que se compara: su nombre, unidad y si bajar es mejorar.
// Bajar mejora el peso, la grasa, la cintura, la cadera y el IMC; subir mejora
// la masa muscular y las circunferencias de brazo, pierna y pecho.
const DATOS: { campo: keyof DiferenciasMedicion; label: string; unidad: string; bajarMejora: boolean }[] = [
    { campo: 'peso_kg', label: 'Peso', unidad: 'kg', bajarMejora: true },
    { campo: 'imc', label: 'IMC', unidad: '', bajarMejora: true },
    { campo: 'porcentaje_grasa', label: 'Grasa corporal', unidad: '%', bajarMejora: true },
    { campo: 'masa_muscular_kg', label: 'Masa muscular', unidad: 'kg', bajarMejora: false },
    { campo: 'circunf_cintura_cm', label: 'Cintura', unidad: 'cm', bajarMejora: true },
    { campo: 'circunf_cadera_cm', label: 'Cadera', unidad: 'cm', bajarMejora: true },
    { campo: 'circunf_brazo_cm', label: 'Brazo', unidad: 'cm', bajarMejora: false },
    { campo: 'circunf_pierna_cm', label: 'Pierna', unidad: 'cm', bajarMejora: false },
    { campo: 'circunf_pecho_cm', label: 'Pecho', unidad: 'cm', bajarMejora: false },
];

// "+1.5 kg", "-2 cm" o "0 %". Se redondea a 2 decimales para evitar
// resultados como 0.30000000000000004.
const formatearDiferencia = (valor: number, unidad: string) => {
    const redondeado = Math.round(valor * 100) / 100;
    const signo = redondeado > 0 ? '+' : '';
    return `${signo}${redondeado}${unidad ? ` ${unidad}` : ''}`;
};

// FilaDiferencia: un dato con su cambio en verde (mejora), rojo (empeora) o
// gris (sin cambio).
interface FilaDiferenciaProps {
    label: string;
    valor: number;
    unidad: string;
    bajarMejora: boolean;
}

const FilaDiferencia = ({ label, valor, unidad, bajarMejora }: FilaDiferenciaProps) => {
    const mejora = bajarMejora ? valor < 0 : valor > 0;
    const empeora = bajarMejora ? valor > 0 : valor < 0;

    return (
        <View style={styles.filaDiferencia}>
            <Text style={styles.linea}>{label}</Text>
            {/* Estilos condicionales en arreglo: el último que aplica gana. */}
            <Text style={[styles.diferencia, mejora && styles.mejora, empeora && styles.empeora]}>
                {formatearDiferencia(valor, unidad)}
            </Text>
        </View>
    );
};

// CompararMediciones: elegir dos mediciones de la lista y ver qué cambió.
export const CompararMediciones = () => {
    const { mediciones, cargando, error, recargar } = useMediciones();
    const [elegidas, setElegidas] = useState<string[]>([]); // fechas "AAAA-MM-DD"
    const [resultado, setResultado] = useState<MedicionComparativa | null>(null);
    const [comparando, setComparando] = useState(false);
    const [errorComparar, setErrorComparar] = useState('');

    useEffect(() => {
        recargar();
    }, [recargar]);

    // Tocar una medición la elige o la quita. Si ya hay dos, la nueva reemplaza
    // a la que se eligió primero.
    const alternar = (medicion: Medicion) => {
        setResultado(null);
        setErrorComparar('');
        setElegidas((actuales) => {
            if (actuales.includes(medicion.fecha)) {
                return actuales.filter((fecha) => fecha !== medicion.fecha);
            }
            return [...actuales, medicion.fecha].slice(-2);
        });
    };

    const comparar = async () => {
        setErrorComparar('');
        setComparando(true);
        try {
            setResultado(await compararMediciones(elegidas[0], elegidas[1]));
        } catch (e) {
            // 400 (fechas iguales) y 404 (fecha sin medición) traen el motivo
            // en español; getErrorMessage lo devuelve tal cual.
            setErrorComparar(getErrorMessage(e));
        } finally {
            setComparando(false);
        }
    };

    if (cargando) {
        return <Loading />;
    }

    if (mediciones.length < 2) {
        return (
            <Screen>
                <EmptyState
                    message={error !== '' ? error : 'Necesitas al menos dos mediciones para comparar.'}
                    actionLabel={error !== '' ? 'Reintentar' : ''}
                    onAction={recargar}
                />
            </Screen>
        );
    }

    // Solo los datos que tienen valor en las dos mediciones.
    const diferencias = resultado
        ? DATOS.filter(({ campo }) => resultado.diferencias[campo] !== null)
        : [];

    const encabezado = (
        <View>
            {resultado ? (
                <>
                    <TarjetaMedicion medicion={resultado.medicion_anterior} title="Antes" />
                    <TarjetaMedicion medicion={resultado.medicion_reciente} title="Después" />
                    <View style={styles.tarjeta}>
                        <Text style={styles.titulo}>Diferencias</Text>
                        {diferencias.map(({ campo, label, unidad, bajarMejora }) => (
                            <FilaDiferencia
                                key={campo}
                                label={label}
                                valor={resultado.diferencias[campo] as number}
                                unidad={unidad}
                                bajarMejora={bajarMejora}
                            />
                        ))}
                    </View>
                </>
            ) : (
                <Text style={styles.ayuda}>
                    Toca dos mediciones para compararlas ({elegidas.length} de 2).
                </Text>
            )}

            {errorComparar !== '' && <Text style={styles.error}>{errorComparar}</Text>}

            {!resultado && (
                <StyledButton
                    label={comparando ? 'Comparando...' : 'Comparar'}
                    handleClick={comparar}
                    disabled={elegidas.length < 2 || comparando}
                />
            )}
            <Text style={styles.subtitulo}>Mediciones</Text>
        </View>
    );

    return (
        <Screen>
            <FlatList
                data={mediciones}
                keyExtractor={(medicion) => medicion.id}
                ListHeaderComponent={encabezado}
                contentContainerStyle={styles.lista}
                renderItem={({ item }) => {
                    const elegida = elegidas.includes(item.fecha);
                    return (
                        <Pressable
                            style={({ pressed }) => [
                                styles.fila,
                                elegida && styles.filaElegida,
                                pressed && styles.presionada,
                            ]}
                            onPress={() => alternar(item)}
                        >
                            <Text style={styles.linea}>{formatearFecha(item.fecha)}</Text>
                            <Text style={[styles.linea, elegida && styles.textoElegido]}>
                                {item.peso_kg} kg
                            </Text>
                        </Pressable>
                    );
                }}
            />
        </Screen>
    );
};

const styles = StyleSheet.create({
    lista: { gap: theme.spacing.sm, paddingBottom: theme.spacing.xl },
    ayuda: { color: theme.colors.textMuted, fontSize: theme.fontSize.md, marginBottom: theme.spacing.md },
    error: { color: theme.colors.error, fontSize: theme.fontSize.sm, marginBottom: theme.spacing.md },
    subtitulo: {
        color: theme.colors.text,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
        marginTop: theme.spacing.md,
    },
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
    linea: { color: theme.colors.text, fontSize: theme.fontSize.md },
    filaDiferencia: { flexDirection: 'row', justifyContent: 'space-between' },
    diferencia: { color: theme.colors.textMuted, fontSize: theme.fontSize.md, fontWeight: 'bold' },
    mejora: { color: theme.colors.success },
    empeora: { color: theme.colors.error },
    fila: {
        backgroundColor: theme.colors.surface,
        borderColor: theme.colors.border,
        borderRadius: 12,
        borderWidth: 1,
        flexDirection: 'row',
        justifyContent: 'space-between',
        padding: theme.spacing.md,
    },
    filaElegida: { borderColor: theme.colors.primary, borderWidth: 2 },
    textoElegido: { color: theme.colors.primary, fontWeight: 'bold' },
    presionada: { opacity: 0.7 },
});
