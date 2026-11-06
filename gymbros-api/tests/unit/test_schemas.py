"""Validaciones de entrada (Pydantic) de todos los módulos."""

import uuid
from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegistroRequest
from app.schemas.medicion import MedicionActualizar, MedicionCrear
from app.schemas.rutina import RutinaCreate
from app.schemas.serie import SeriesPayload
from app.schemas.sesion import CalificacionCrear, SesionIniciar
from app.schemas.usuario import UsuarioUpdate
from tests.conftest import hoy_colombia


# --- Auth (RN-21, Ley 1581) -------------------------------------------------
def _registro(**campos):
    datos = {
        "correo": "ana@gymbros-pruebas.com",
        "password": "Clave12345",
        "nombre": "Ana",
        "consentimiento_datos": True,
    }
    datos.update(campos)
    return RegistroRequest(**datos)


@pytest.mark.parametrize("password", ["corta1", "solamenteletras", "1234567890"])
def test_registro_rechaza_password_debil(password):
    with pytest.raises(ValidationError):
        _registro(password=password)


def test_registro_exige_consentimiento():
    with pytest.raises(ValidationError, match="Ley 1581"):
        _registro(consentimiento_datos=False)


def test_registro_limpia_y_exige_nombre():
    assert _registro(nombre="  Ana  ").nombre == "Ana"
    with pytest.raises(ValidationError):
        _registro(nombre="   ")


# --- Usuarios ---------------------------------------------------------------
def test_usuario_update_valida_nombre_y_altura():
    with pytest.raises(ValidationError):
        UsuarioUpdate(nombre="   ")
    with pytest.raises(ValidationError):
        UsuarioUpdate(altura_cm=20)
    assert UsuarioUpdate(nombre="  Juan ").nombre == "Juan"


# --- Mediciones (RN-03 a RN-06, RN-70, H-09) -------------------------------
@pytest.mark.parametrize(
    "campos",
    [
        {"peso_kg": 0},
        {"peso_kg": 0.001},
        {"peso_kg": 1000},
        {"peso_kg": True},
        {"porcentaje_grasa": 100.5},
        {"porcentaje_grasa": -1},
        {"circunf_brazo_cm": 0},
    ],
)
def test_medicion_crear_rechaza_valores_invalidos(campos):
    datos = {"fecha": "2026-01-01T08:00:00-05:00", "peso_kg": 70}
    datos.update(campos)
    with pytest.raises(ValidationError):
        MedicionCrear(**datos)


def test_medicion_actualizar_rechaza_fecha_futura_e_ignora_usuario_id():
    with pytest.raises(ValidationError, match="futura"):
        MedicionActualizar(fecha=hoy_colombia() + timedelta(days=1))

    datos = MedicionActualizar(peso_kg=71, usuario_id=str(uuid.uuid4()))
    assert datos.model_dump(exclude_unset=True) == {"peso_kg": 71}


# --- Rutinas ----------------------------------------------------------------
def test_rutina_exige_al_menos_un_ejercicio():
    with pytest.raises(ValidationError):
        RutinaCreate(nombre="Pierna", ejercicios=[])


# --- Sesiones y series ------------------------------------------------------
def test_sesion_iniciar_exige_zona_horaria_en_iniciada_en():
    with pytest.raises(ValidationError):
        SesionIniciar(idempotency_key="k", iniciada_en="2026-01-01T10:00:00")


def _serie(**campos):
    datos = {
        "ejercicio_id": str(uuid.uuid4()),
        "numero_serie": 1,
        "repeticiones_realizadas": 10,
        "peso_usado_kg": 50,
        "orden": 1,
    }
    datos.update(campos)
    return datos


def test_series_payload_acepta_un_objeto_y_lo_vuelve_lista():
    payload = SeriesPayload(series=_serie())
    assert len(payload.series) == 1


def test_series_payload_rechaza_series_repetidas_en_el_lote():
    serie = _serie()
    with pytest.raises(ValidationError, match="repite"):
        SeriesPayload(series=[serie, dict(serie)])


@pytest.mark.parametrize(
    "campos",
    [
        {"numero_serie": True},
        {"repeticiones_realizadas": False},
        {"peso_usado_kg": True},
        {"orden": True},
        {"repeticiones_realizadas": -1},
        {"peso_usado_kg": 1000},
    ],
)
def test_serie_rechaza_booleanos_y_rangos_invalidos(campos):
    with pytest.raises(ValidationError):
        SeriesPayload(series=[_serie(**campos)])


def test_serie_acepta_cero_repeticiones_y_peso_corporal():
    """RN-45: 0 repeticiones es una serie fallida, no un error."""
    payload = SeriesPayload(series=[_serie(repeticiones_realizadas=0, peso_usado_kg=0)])
    assert payload.series[0].repeticiones_realizadas == 0


@pytest.mark.parametrize("valor", [0, 6, True])
def test_calificacion_fuera_de_rango_o_booleana(valor):
    with pytest.raises(ValidationError):
        CalificacionCrear(calificacion=valor)
