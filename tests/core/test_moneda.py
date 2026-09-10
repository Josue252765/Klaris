"""Tests de core/moneda.py: TasaCambio y conversiones."""

from datetime import date
from decimal import Decimal

import pytest

from core.moneda import Moneda, TasaCambio
from utils.excepciones import MonedaInvalidaError, ValorInvalidoError


def _tasa(
    ref: str = "40",
    diaria: str = "42",
) -> TasaCambio:
    return TasaCambio(
        tasa_referencial=Decimal(ref),
        tasa_referencial_fecha=date(2026, 9, 9),
        tasa_diaria=Decimal(diaria),
        tasa_diaria_fecha=date(2026, 9, 9),
    )


def test_convertir_usd_a_bs_con_diaria() -> None:
    tasa = _tasa()
    resultado = tasa.convertir(Decimal("10"), Moneda.USD, Moneda.BS, "diaria")
    assert resultado == Decimal("420.00")


def test_convertir_bs_a_usd_con_diaria() -> None:
    tasa = _tasa()
    resultado = tasa.convertir(Decimal("420"), Moneda.BS, Moneda.USD, "diaria")
    assert resultado == Decimal("10.00")


def test_convertir_usd_a_bs_con_referencial() -> None:
    tasa = _tasa()
    resultado = tasa.convertir(Decimal("10"), Moneda.USD, Moneda.BS, "referencial")
    assert resultado == Decimal("400.00")


def test_convertir_bs_a_usd_con_referencial() -> None:
    tasa = _tasa()
    resultado = tasa.convertir(Decimal("400"), Moneda.BS, Moneda.USD, "referencial")
    assert resultado == Decimal("10.00")


def test_convertir_mismo_origen_destino_lanza() -> None:
    tasa = _tasa()
    with pytest.raises(MonedaInvalidaError):
        tasa.convertir(Decimal("10"), Moneda.USD, Moneda.USD, "diaria")


def test_tasa_referencial_cero_lanza() -> None:
    with pytest.raises(ValorInvalidoError):
        _tasa(ref="0")


def test_tasa_diaria_negativa_lanza() -> None:
    with pytest.raises(ValorInvalidoError):
        _tasa(diaria="-1")


def test_tasa_referencial_float_rechazado() -> None:
    with pytest.raises(ValorInvalidoError):
        TasaCambio(
            tasa_referencial=40.0,  # type: ignore[arg-type]
            tasa_referencial_fecha=date(2026, 9, 9),
            tasa_diaria=Decimal("42"),
            tasa_diaria_fecha=date(2026, 9, 9),
        )


def test_convertir_redondea_half_up() -> None:
    tasa = TasaCambio(
        tasa_referencial=Decimal("40"),
        tasa_referencial_fecha=date(2026, 9, 9),
        tasa_diaria=Decimal("3"),
        tasa_diaria_fecha=date(2026, 9, 9),
    )
    resultado = tasa.convertir(Decimal("10.005"), Moneda.USD, Moneda.BS, "diaria")
    assert resultado == Decimal("30.02")
