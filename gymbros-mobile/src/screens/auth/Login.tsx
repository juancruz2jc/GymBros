import { useNavigation } from '@react-navigation/native';
import axios from 'axios';
import { useState } from 'react';
import { StyleSheet, Text } from 'react-native';
import { FormScroll } from '../../components/FormScroll';
import { Input } from '../../components/Input';
import { Screen } from '../../components/Screen';
import { StyledButton } from '../../components/StyledButton';
import { TextLink } from '../../components/TextLink';
import { useAuth } from '../../hooks/useAuth';
import { getErrorMessage } from '../../services/api';
import { theme } from '../../theme/theme';
import { validarCorreo, validarRequerido } from '../../utils/validaciones';

// Login: inicio de sesión con correo y contraseña (GYM-184).
export const Login = () => {
    const { login } = useAuth();
    const navigation = useNavigation();

    // Lo que escribe la persona.
    const [correo, setCorreo] = useState('');
    const [password, setPassword] = useState('');
    // Errores de cada campo (validación local) y error que responde la API.
    const [errorCorreo, setErrorCorreo] = useState('');
    const [errorPassword, setErrorPassword] = useState('');
    const [error, setError] = useState('');
    const [enviando, setEnviando] = useState(false);

    // Revisa los campos antes de llamar a la API.
    const formularioValido = () => {
        const deCorreo = validarCorreo(correo);
        const dePassword = validarRequerido(password, 'Escribe tu contraseña.');
        setErrorCorreo(deCorreo);
        setErrorPassword(dePassword);
        return deCorreo === '' && dePassword === '';
    };

    const entrar = async () => {
        setError('');
        if (!formularioValido()) {
            return;
        }
        setEnviando(true);
        try {
            // Si funciona, RootNavigator cambia solo a las pestañas.
            await login({ correo: correo.trim(), password });
        } catch (e) {
            // En el login, un 401 significa que los datos no coinciden.
            if (axios.isAxiosError(e) && e.response?.status === 401) {
                setError('Correo o contraseña incorrectos');
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
                    label="Correo"
                    value={correo}
                    onChangeText={setCorreo}
                    error={errorCorreo}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoComplete="email"
                />
                <Input
                    label="Contraseña"
                    value={password}
                    onChangeText={setPassword}
                    error={errorPassword}
                    secureTextEntry
                    autoCapitalize="none"
                    autoComplete="current-password"
                />
                {error !== '' && <Text style={styles.error}>{error}</Text>}
                <StyledButton
                    label={enviando ? 'Entrando...' : 'Entrar'}
                    handleClick={entrar}
                    disabled={enviando}
                />
                <TextLink
                    label="Crear cuenta"
                    handleClick={() => navigation.navigate('Registro')}
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
