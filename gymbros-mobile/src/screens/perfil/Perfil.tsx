import { useEffect, useState } from 'react';
import { Alert, Platform, StyleSheet, Text, View } from 'react-native';
import { Card } from '../../components/Card';
import { ChipOption, Chips } from '../../components/Chips';
import { FormScroll } from '../../components/FormScroll';
import { Input } from '../../components/Input';
import { Loading } from '../../components/Loading';
import { Screen } from '../../components/Screen';
import { StyledButton } from '../../components/StyledButton';
import { useAuth } from '../../hooks/useAuth';
import { usePerfil } from '../../hooks/usePerfil';
import { theme } from '../../theme/theme';
import { UsuarioActualizar } from '../../types/usuario';
import { validarAltura, validarNombrePerfil } from '../../utils/validaciones';

const OPCIONES_SEXO: ChipOption[] = [
    { value: 'femenino', label: 'Femenino' },
    { value: 'masculino', label: 'Masculino' },
    { value: 'otro', label: 'Otro' },
];

const PREGUNTA_CIERRE = '¿Quieres cerrar sesión?';

// Perfil: ver y editar los datos personales, y cerrar sesión (GYM-190).
export const Perfil = () => {
    const { logout } = useAuth();
    const { perfil, cargando, guardando, error, recargar, actualizar } = usePerfil();

    // Lo que hay escrito en el formulario.
    const [nombre, setNombre] = useState('');
    const [sexo, setSexo] = useState<string | null>(null);
    const [altura, setAltura] = useState('');
    const [errorNombre, setErrorNombre] = useState('');
    const [errorAltura, setErrorAltura] = useState('');
    const [guardado, setGuardado] = useState(false); // muestra el mensaje de éxito
    const [cerrando, setCerrando] = useState(false);

    // Cuando llega el perfil (al cargar o al guardar), se llena el formulario.
    useEffect(() => {
        if (perfil) {
            setNombre(perfil.nombre);
            setSexo(perfil.sexo);
            setAltura(perfil.altura_cm?.toString() ?? '');
        }
    }, [perfil]);

    const cerrarSesion = async () => {
        setCerrando(true);
        await logout(); // al terminar, RootNavigator vuelve a Login
    };

    const confirmarCierre = () => {
        // Alert no hace nada en web: allí se usa la confirmación del navegador.
        if (Platform.OS === 'web') {
            if (window.confirm(PREGUNTA_CIERRE)) {
                cerrarSesion();
            }
            return;
        }
        Alert.alert('Cerrar sesión', PREGUNTA_CIERRE, [
            { text: 'Cancelar', style: 'cancel' },
            { text: 'Cerrar sesión', style: 'destructive', onPress: cerrarSesion },
        ]);
    };

    const botonCerrarSesion = (
        <View style={styles.logout}>
            <StyledButton
                label="Cerrar sesión"
                color={theme.colors.error}
                handleClick={confirmarCierre}
                disabled={cerrando || guardando}
            />
        </View>
    );

    if (cargando) {
        return (
            <Screen>
                <Loading />
            </Screen>
        );
    }

    // No se pudo cargar: se puede reintentar o cerrar sesión.
    if (!perfil) {
        return (
            <Screen>
                <Text style={styles.error}>{error}</Text>
                <StyledButton label="Reintentar" handleClick={recargar} />
                {botonCerrarSesion}
            </Screen>
        );
    }

    // Solo los campos distintos a lo guardado.
    const cambios: UsuarioActualizar = {};
    if (nombre.trim() !== perfil.nombre) {
        cambios.nombre = nombre.trim();
    }
    if (sexo !== perfil.sexo) {
        cambios.sexo = sexo;
    }
    if (altura.trim() !== (perfil.altura_cm?.toString() ?? '')) {
        // Vacía significa borrar el dato.
        cambios.altura_cm = altura.trim() === '' ? null : Number(altura);
    }
    const hayCambios = Object.keys(cambios).length > 0;

    // Un valor guardado que no está entre las opciones (por ejemplo "M").
    const sexoSinOpcion =
        perfil.sexo !== null && !OPCIONES_SEXO.some((opcion) => opcion.value === perfil.sexo);

    // Tocar la opción ya marcada la quita. Si lo guardado no era una opción, se
    // vuelve a ese valor para no borrarlo sin querer.
    const elegirSexo = (valor: string) => {
        const sinElegir = sexoSinOpcion ? perfil.sexo : null;
        setSexo(valor === sexo ? sinElegir : valor);
        setGuardado(false);
    };

    const guardar = async () => {
        setGuardado(false);
        // Se valida solo lo que cambió.
        const deNombre = cambios.nombre !== undefined ? validarNombrePerfil(nombre) : '';
        const deAltura = cambios.altura_cm !== undefined ? validarAltura(altura) : '';
        setErrorNombre(deNombre);
        setErrorAltura(deAltura);
        if (deNombre !== '' || deAltura !== '') {
            return;
        }
        setGuardado(await actualizar(cambios));
    };

    return (
        <Screen>
            <FormScroll>
                <Card title="Cuenta">
                    <Text style={styles.name}>{perfil.nombre}</Text>
                    {/* El correo identifica la cuenta: no se edita. */}
                    <Text style={styles.email}>{perfil.correo}</Text>
                </Card>

                <Input
                    label="Nombre"
                    value={nombre}
                    onChangeText={(texto) => {
                        setNombre(texto);
                        setGuardado(false);
                    }}
                    error={errorNombre}
                    autoCapitalize="words"
                    autoComplete="name"
                />
                <Chips
                    label="Sexo (opcional)"
                    options={OPCIONES_SEXO}
                    selected={sexo}
                    handleChange={elegirSexo}
                    disabled={guardando}
                />
                {sexoSinOpcion && sexo === perfil.sexo && (
                    <Text style={styles.help}>Valor guardado: {perfil.sexo}</Text>
                )}
                <Input
                    label="Altura (cm)"
                    value={altura}
                    onChangeText={(texto) => {
                        setAltura(texto);
                        setGuardado(false);
                    }}
                    error={errorAltura}
                    keyboardType="number-pad"
                />
                <Text style={styles.help}>Se usa para calcular tu IMC</Text>

                {error !== '' && <Text style={styles.error}>{error}</Text>}
                {guardado && <Text style={styles.success}>Cambios guardados</Text>}

                <StyledButton
                    label={guardando ? 'Guardando...' : 'Guardar'}
                    handleClick={guardar}
                    disabled={guardando || !hayCambios}
                />
                {botonCerrarSesion}
            </FormScroll>
        </Screen>
    );
};

const styles = StyleSheet.create({
    name: {
        color: theme.colors.text,
        fontSize: theme.fontSize.lg,
        fontWeight: 'bold',
    },
    email: { color: theme.colors.textMuted, fontSize: theme.fontSize.sm },
    help: {
        color: theme.colors.textMuted,
        fontSize: theme.fontSize.sm,
        marginBottom: theme.spacing.md,
        marginTop: -theme.spacing.sm, // pegado al campo de arriba
    },
    error: {
        color: theme.colors.error,
        fontSize: theme.fontSize.sm,
        marginBottom: theme.spacing.md,
    },
    success: {
        color: theme.colors.success,
        fontSize: theme.fontSize.sm,
        fontWeight: 'bold',
        marginBottom: theme.spacing.md,
    },
    logout: { marginTop: theme.spacing.xl },
});
