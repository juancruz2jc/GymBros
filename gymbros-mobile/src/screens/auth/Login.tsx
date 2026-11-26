import { useState } from 'react';
import { StyleSheet, Text } from 'react-native';
import { Input } from '../../components/Input';
import { Screen } from '../../components/Screen';
import { StyledButton } from '../../components/StyledButton';
import { useAuth } from '../../hooks/useAuth';
import { getErrorMessage } from '../../services/api';
import { theme } from '../../theme/theme';

// Login: formulario mínimo para iniciar sesión (se completa en GYM-184).
export const Login = () => {
    const { login } = useAuth();
    const [correo, setCorreo] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [enviando, setEnviando] = useState(false);

    const entrar = async () => {
        setError('');
        setEnviando(true);
        try {
            // Si funciona, RootNavigator cambia solo a las pestañas.
            await login({ correo: correo.trim(), password });
        } catch (e) {
            setError(getErrorMessage(e));
        } finally {
            setEnviando(false);
        }
    };

    return (
        <Screen>
            <Input label="Correo" value={correo} onChangeText={setCorreo} />
            <Input label="Contraseña" value={password} onChangeText={setPassword} secureTextEntry />
            {error !== '' && <Text style={styles.error}>{error}</Text>}
            <StyledButton
                label={enviando ? 'Entrando...' : 'Entrar'}
                handleClick={entrar}
                disabled={enviando}
            />
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
