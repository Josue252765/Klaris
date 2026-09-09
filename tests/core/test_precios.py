"""Tests de core/precios.py: CalculadoraPrecios."""

from decimal import Decimal

import pytest

from core.precios import CalculadoraPrecios
from utils.excepciones import ValorInvalidoError


def test_precio_venta_con_margen_30() -> None:
    resultado = CalculadoraPrecios.precio_venta(Decimal("100"), Decimal("30"))
    assert resultado == Decimal("130.00")


def test_precio_mayorista_con_margen_propio() -> None:
    resultado = CalculadoraPrecios.precio_mayorista(Decimal("100"), Decimal("10"))
    assert resultado == Decimal("110.00")


def test_precio_venta_es_decimal_exacto_sin_float() -> None:
    resultado = CalculadoraPrecios.precio_venta(Decimal("0.335"), Decimal("0"))
    assert isinstance(resultado, Decimal)
    assert resultado == Decimal("0.34")


def test_redondeo_half_up_dos_decimales() -> None:
    resultado = CalculadoraPrecios.precio_venta(Decimal("10.005"), Decimal("0"))
    assert resultado == Decimal("10.01")


def test_margen_negativo_esta_permitido() -> None:
    resultado = CalculadoraPrecios.precio_venta(Decimal("100"), Decimal("-10"))
    assert resultado == Decimal("90.00")


def test_margen_real() -> None:
    margen = CalculadoraPrecios.margen_real(Decimal("100"), Decimal("130"))
    assert margen == Decimal("30.00")


def test_margen_real_con_costo_cero_lanza_valor_invalido() -> None:
    with pytest.raises(ValorInvalidoError):
        CalculadoraPrecios.margen_real(Decimal("0"), Decimal("5"))