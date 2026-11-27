import { RouteProp, useNavigation, useRoute } from '@react-navigation/native';
import axios from 'axios';
import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { Input } from '../../components/Input';
import { Loading } from '../../components/Loading';
import { Screen } from '../../components/Screen';
import { StyledButton } from '../../components/StyledButton';
import { MainStackParamList } from '../../navigation/types';
import { getErrorMessage } from '../../services/api';
import { crearMedicion, editarMedicion, obtenerMedicion } from '../../services/medicionService';
import { theme } from '../../theme/theme';
import { CampoOpcional, MedicionDatos } from '../../types/medicion';

// Campos opcionales del formulario, en el orden en que se muestran.
const OPCIONALES: { campo: CampoOpcional; label: string; seccion: string }[] = [
    { campo: 'porcentaje_grasa', label: 'Grasa corporal (%)', seccion: 'Composición corporal' },
    { campo: 'masa_muscular_kg', label: 'Masa muscular (kg)', seccion: 'Composición corporal' },
    { campo: 'circunf_cintura_cm', label: 'Cintura (cm)', seccion: 'Circunferencias' },
    { campo: 'circunf_cadera_cm', label: 'Cadera (cm)', seccion: 'Circunferencias' },
    { campo: 'circunf_brazo_cm', label: 'Brazo (cm)', seccion: 'Circunferencias' },
    { campo: 'circunf_pierna_cm', label: 'Pierna (cm)', seccion: 'Circunferencias' },
    { campo: 'circunf_pecho_cm', label: 'Pecho (cm)', seccion: 'Circunferencias' },
];

type Valores = Record<CampoOpcional, string>;

const VALORES_VACIOS: Valores = {
    porcentaje_grasa: '',
    masa_muscular_kg: '',
    circunf_cintura_cm: '',
    circunf_cadera_cm: '',
    circunf_brazo_cm: '',
    circunf_pierna_cm: '',
    circunf_pecho_cm: '',
};

// Hoy en la hora del celular, como "YYYY-MM-DD". No se usa toISOString(),
// que da la fecha en UTC (en la noche ya sería mañana).
const hoy = () => {
    const ahora = new Date();
    const mes = String(ahora.getMonth() + 1).padStart(2, '0');
    const dia = String(ahora.getDate()).padStart(2, '0');
    return `${ahora.getFullYear()}-${mes}-${dia}`;
};

// true si el texto es una fecha real con formato "YYYY-MM-DD".
const esFechaValida = (texto: string) => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(texto)) {
        return false;
    }
    const [anio, mes, dia] = texto.split('-').map(Number);
    const fecha = new Date(anio, mes - 1, dia);
    return fecha.getMonth() === mes - 1 && fecha.getDate() === dia; // descarta 2026-02-31
};

// "72,5" o "72.5" -> 72.5. Devuelve NaN si no es un número.
const aNumero = (texto: string) => Number(texto.trim().replace(',', '.'));

// RegistrarMedicion: formulario para registrar una medición o, si llega
// `medicionId`, para editarla.
export const RegistrarMedicion = () => {
    const navigation = useNavigation();
    const { params } = useRoute<RouteProp<MainStackParamList, 'RegistrarMedicion'>>();
    const medicionId = params?.medicionId;
    const editando = medicionId !== undefined;

    const [fecha, setFecha] = useState(hoy());
    const [peso, setPeso] = useState('');
    const [opcionales, setOpcionales] = useState<Valores>(VALORES_VACIOS);
    const [errores, setErrores] = useState<Record<string, string>>({});
    const [errorGeneral, setErrorGeneral] = useState('');
    const [cargando, setCargando] = useState(editando);
    const [guardando, setGuardando] = useState(false);

    // En modo edición: cambiar el título y llenar el formulario.
    useEffect(() => {
        if (!medicionId) {
            return;
        }
        navigation.setOptions({ title: 'Editar medición' });

        const cargar = async () => {
            try {
                const medicion = await obtenerMedicion(medicionId);
                setFecha(medicion.fecha);
                setPeso(String(medicion.peso_kg));
                const valores = { ...VALORES_VACIOS };
                OPCIONALES.forEach(({ campo }) => {
                    const valor = medicion[campo];
                    valores[campo] = valor === null ? '' : String(valor);
                });
                setOpcionales(valores);
            } catch (e) {
                setErrorGeneral(getErrorMessage(e));
            } finally {
                setCargando(false);
            }
        };
        cargar();
    }, [medicionId, navigation]);

    const cambiarOpcional = (campo: CampoOpcional, texto: string) => {
        setOpcionales((actuales) => ({ ...actuales, [campo]: texto }));
    };

    // Validación local. Devuelve los datos listos para enviar, o null si hay
    // errores (y los deja en `errores` para mostrarlos debajo de cada campo).
    const validar = (): MedicionDatos | null => {
        const nuevos: Record<string, string> = {};

        if (!esFechaValida(fecha)) {
            nuevos.fecha = 'Escribe la fecha como AAAA-MM-DD.';
        } else if (fecha > hoy()) {
            // Con el formato AAAA-MM-DD, comparar textos ordena igual que las fechas.
            nuevos.fecha = 'La fecha no puede ser futura.';
        }

        const pesoKg = aNumero(peso);
        if (peso.trim() === '') {
            nuevos.peso = 'El peso es obligatorio.';
        } else if (Number.isNaN(pesoKg) || pesoKg <= 0) {
            nuevos.peso = 'El peso debe ser mayor que 0.';
        }

        const datos: MedicionDatos = { fecha, peso_kg: pesoKg };
        OPCIONALES.forEach(({ campo }) => {
            const texto = opcionales[campo];
            if (texto.trim() === '') {
                return; // opcional vacío: no se envía
            }
            const valor = aNumero(texto);
            if (Number.isNaN(valor) || valor <= 0) {
                nuevos[campo] = 'Debe ser un número mayor que 0.';
            } else if (campo === 'porcentaje_grasa' && valor > 100) {
                nuevos[campo] = 'Debe estar entre 0 y 100.';
            } else {
                datos[campo] = valor;
            }
        });

        setErrores(nuevos);
        return Object.keys(nuevos).length === 0 ? datos : null;
    };

    const guardar = async () => {
        setErrorGeneral('');
        const datos = validar();
        if (!datos) {
            return;
        }

        setGuardando(true);
        try {
            if (medicionId) {
                await editarMedicion(medicionId, datos);
            } else {
                await crearMedicion(datos);
            }
            // Progreso recarga sola al volver a mostrarse (useFocusEffect).
            navigation.goBack();
        } catch (e) {
            if (axios.isAxiosError(e) && e.response?.status === 409) {
                setErrorGeneral('Ya registraste una medición ese día');
            } else {
                setErrorGeneral(getErrorMessage(e));
            }
            setGuardando(false);
        }
    };

    if (cargando) {
        return <Loading />;
    }

    return (
        <Screen>
            <ScrollView keyboardShouldPersistTaps="handled">
                <Input
                    label="Fecha (AAAA-MM-DD)"
                    value={fecha}
                    onChangeText={setFecha}
                    error={errores.fecha}
                    keyboardType="numbers-and-punctuation"
                />
                <Input
                    label="Peso (kg) *"
                    value={peso}
                    onChangeText={setPeso}
                    error={errores.peso}
                    keyboardType="decimal-pad"
                />

                {OPCIONALES.map(({ campo, label, seccion }, i) => (
                    <View key={campo}>
                        {/* El título de la sección va antes de su primer campo. */}
                        {(i === 0 || OPCIONALES[i - 1].seccion !== seccion) && (
                            <Text style={styles.seccion}>{seccion} (opcional)</Text>
                        )}
                        <Input
                            label={label}
                            value={opcionales[campo]}
                            onChangeText={(texto) => cambiarOpcional(campo, texto)}
                            error={errores[campo]}
                            keyboardType="decimal-pad"
                        />
                    </View>
                ))}

                {errorGeneral !== '' && <Text style={styles.error}>{errorGeneral}</Text>}

                <StyledButton
                    label={guardando ? 'Guardando...' : editando ? 'Guardar cambios' : 'Registrar medición'}
                    handleClick={guardar}
                    disabled={guardando}
                />
            </ScrollView>
        </Screen>
    );
};

const styles = StyleSheet.create({
    seccion: {
        color: theme.colors.text,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
        marginBottom: theme.spacing.sm,
        marginTop: theme.spacing.sm,
    },
    error: {
        color: theme.colors.error,
        fontSize: theme.fontSize.sm,
        marginBottom: theme.spacing.md,
    },
});
