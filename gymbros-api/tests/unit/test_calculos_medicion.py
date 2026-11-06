"""Cálculo y clasificación del IMC (RN-09 a RN-13)."""

import pytest

from app.services.medicion_service import calcular_imc, clasificar_imc


@pytest.mark.parametrize(
    ("peso", "altura", "esperado"),
    [
        (70, 175, 22.9),
        (100, 180, 30.9),
        (50.5, 160, 19.7),
    ],
)
def test_calcular_imc_redondea_a_un_decimal(peso, altura, esperado):
    assert calcular_imc(peso, altura) == esperado


@pytest.mark.parametrize("altura", [None, 0, -10])
def test_calcular_imc_sin_altura_valida_es_none(altura):
    assert calcular_imc(70, altura) is None


@pytest.mark.parametrize(
    ("imc", "categoria"),
    [
        (None, None),
        (18.4, "bajo_peso"),
        (18.5, "normal"),
        (24.9, "normal"),
        (25.0, "sobrepeso"),
        (29.9, "sobrepeso"),
        (30.0, "obesidad"),
    ],
)
def test_clasificar_imc_limites_oms(imc, categoria):
    assert clasificar_imc(imc) == categoria


def test_clasificacion_usa_el_imc_redondeado():
    """RN-13: un IMC de 24.95 se muestra como 25.0 y debe salir `sobrepeso`."""
    assert calcular_imc(76.4, 175) == 24.9  # 24.946...
    imc = calcular_imc(76.41, 175)  # 24.950... -> 25.0 (ROUND_HALF_UP)
    assert imc == 25.0
    assert clasificar_imc(imc) == "sobrepeso"
