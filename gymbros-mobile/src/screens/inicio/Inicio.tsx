import { useState } from 'react';
import { Text } from 'react-native';
import { Screen } from '../../components/Screen';
import { StyledButton } from '../../components/StyledButton';
import { useAuth } from '../../hooks/useAuth';

export const Inicio = () => {
    const { usuario, logout } = useAuth();
    const [cerrando, setCerrando] = useState(false);

    // TEMPORAL (GYM-183): botón para probar el cierre de sesión.
    const cerrarSesion = async () => {
        setCerrando(true);
        await logout(); // al terminar, RootNavigator vuelve a Login
    };

    return (
        <Screen>
            <Text>Inicio</Text>
            <Text>Sesión de {usuario?.nombre}</Text>
            <StyledButton label="Cerrar sesión" handleClick={cerrarSesion} disabled={cerrando} />
        </Screen>
    );
};
