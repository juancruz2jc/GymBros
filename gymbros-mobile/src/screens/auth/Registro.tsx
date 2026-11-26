import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import axios from 'axios';
import { useState } from 'react';
import { StyleSheet, Text } from 'react-native';
import { Checkbox } from '../../components/Checkbox';
import { FormScroll } from '../../components/FormScroll';
import { Input } from '../../components/Input';
import { Screen } from '../../components/Screen';
import { StyledButton } from '../../components/StyledButton';
import { TextLink } from '../../components/TextLink';
import { useAuth } from '../../hooks/useAuth';
import { AuthStackParamList } from '../../navigation/types';
import { getErrorMessage } from '../../services/api';
import { theme } from '../../theme/theme';
import {
    validarConfirmacion,
    validarCorreo,
    validarNombre,
    validarPasswordNueva,
} from '../../utils/validaciones';

// Mensajes de error de cada campo; '' significa que no hay error.
const SIN_ERRORES = { nombre: '', correo: '', password: '', confirmacion: '' };

// Registro: crea la cuenta y entra directo a la app (GYM-185).
export const Registro = () => {
    const { registrar } = useAuth();
    const navigation = useNavigation<NativeStackNavigationProp<AuthStackParamList>>();

    // Lo que escribe la persona.
    const [nombre, setNombre] = useState('');
    const [correo, setCorreo] = useState('');
    const [password, setPassword] = useState('');
    const [confirmacion, setConfirmacion] = useState('');
    const [consentimiento, setConsentimiento] = useState(false);
    // Errores de la validación local y error que responde la API.
    const [errores, setErrores] = useState(SIN_ERRORES);
    const [error, setError] = useState('');
    const [enviando, setEnviando] = useState(false);

    // Revisa todos los campos antes de llamar a la API.
    const formularioValido = () => {
        const nuevos = {
            nombre: validarNombre(nombre),
            correo: validarCorreo(correo),
            password: validarPasswordNueva(password),
            confirmacion: validarConfirmacion(password, confirmacion),
        };
        setErrores(nuevos);
        // Es válido si todos los mensajes están vacíos.
        return Object.values(nuevos).every((mensaje) => mensaje === '');
    };

    const crearCuenta = async () => {
        setError('');
        if (!formularioValido()) {
            return;
        }
        setEnviando(true);
        try {
            // La API deja la sesión iniciada: RootNavigator pasa a las pestañas.
            await registrar({
                nombre: nombre.trim(),
                correo: correo.trim(),
                password,
                consentimiento_datos: consentimiento,
            });
        } catch (e) {
            // 409: ya existe una cuenta con ese correo.
            if (axios.isAxiosError(e) && e.response?.status === 409) {
                setError('Este correo ya está registrado');
            } else {
                setError(getErrorMessage(e));
            }
        } finally {
            setEnviando(false);
        }
    };

    return (
        <Screen>
            <FormScroll>
                <Input
                    label="Nombre"
                    value={nombre}
                    onChangeText={setNombre}
                    error={errores.nombre}
                    autoCapitalize="words"
                    autoComplete="name"
                />
                <Input
                    label="Correo"
                    value={correo}
                    onChangeText={setCorreo}
                    error={errores.correo}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoComplete="email"
                />
                <Input
                    label="Contraseña"
                    value={password}
                    onChangeText={setPassword}
                    error={errores.password}
                    secureTextEntry
                    autoCapitalize="none"
                    autoComplete="new-password"
                />
                <Input
                    label="Confirmar contraseña"
                    value={confirmacion}
                    onChangeText={setConfirmacion}
                    error={errores.confirmacion}
                    secureTextEntry
                    autoCapitalize="none"
                    autoComplete="new-password"
                />
                {/* Ley 1581: sin consentimiento no se puede crear la cuenta. */}
                <Checkbox
                    label="Acepto el tratamiento de mis datos personales (Ley 1581)."
                    checked={consentimiento}
                    handleChange={setConsentimiento}
                    disabled={enviando}
                />
                {error !== '' && <Text style={styles.error}>{error}</Text>}
                <StyledButton
                    label={enviando ? 'Creando cuenta...' : 'Crear cuenta'}
                    handleClick={crearCuenta}
                    disabled={!consentimiento || enviando}
                />
                {/* popTo vuelve al Login que ya está debajo, sin abrir otro. */}
                <TextLink
                    label="Ya tengo cuenta"
                    handleClick={() => navigation.popTo('Login')}
                    disabled={enviando}
                />
            </FormScroll>
        </Screen>
    );
};

const styles = StyleSheet.create({
    error: {
        color: theme.colors.error,
        fontSize: theme.fontSize.sm,
        marginBottom: theme.spacing.md,
    },
});
