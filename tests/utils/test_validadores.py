"""Tests de utils/validadores.py: validación de texto, montos y opciones."""

from decimal import Decimal

import pytest

from utils.validadores import (
    validar_entero_positivo,
    validar_monto_no_negativo,
    validar_monto_positivo,
    validar_opcion,
    validar_texto_longitud,
    validar_texto_no_vacio,
)


def test_texto_no_vacio_devuelve_limpio() -> None:
    assert validar_texto_no_vacio("  hola  ") == "hola"


def test_texto_no_vacio_vacio_lanza() -> None:
    with pytest.raises(ValueError):
        validar_texto_no_vacio("   ")


def test_texto_no_vacio_none_lanza() -> None:
    with pytest.raises(ValueError):
        validar_texto_no_vacio(None)  # type: ignore[arg-type]


def test_texto_longitud_valido() -> None:
    assert validar_texto_longitud("abc", 10) == "abc"


def test_texto_longitud_excede_lanza() -> None:
    with pytest.raises(ValueError):
        validar_texto_longitud("a" * 11, 10)


def test_monto_positivo_valido() -> None:
    assert validar_monto_positivo(Decimal("10.50")) == Decimal("10.50")


def test_monto_positivo_cero_lanza() -> None:
    with pytest.raises(ValueError):
        validar_monto_positivo(Decimal("0"))


def test_monto_positivo_negativo_lanza() -> None:
    with pytest.raises(ValueError):
        validar_monto_positivo(Decimal("-1"))


def test_monto_positivo_float_lanza() -> None:
    with pytest.raises(TypeError):
        validar_monto_positivo(10.5)


def test_monto_no_negativo_cero_ok() -> None:
    assert validar_monto_no_negativo(Decimal("0")) == Decimal("0")


def test_monto_no_negativo_negativo_lanza() -> None:
    with pytest.raises(ValueError):
        validar_monto_no_negativo(Decimal("-5"))


def test_opcion_valida() -> None:
    assert validar_opcion("efectivo_usd", {"efectivo_usd", "pago_movil"}) == "efectivo_usd"


def test_opcion_invalida_lanza() -> None:
    with pytest.raises(ValueError):
        validar_opcion("cripto", {"efectivo_usd", "pago_movil"})


def test_entero_positivo_valido() -> None:
    assert validar_entero_positivo(5) == 5


def test_entero_positivo_cero_lanza() -> None:
    with pytest.raises(ValueError):
        validar_entero_positivo(0)


def test_entero_positivo_bool_lanza() -> None:
    with pytest.raises(ValueError):
        validar_entero_positivo(True)