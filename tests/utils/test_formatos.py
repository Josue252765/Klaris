"""Tests de utils/formatos.py: formateo de moneda y fechas."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from core.moneda import Moneda
from utils.formatos import formatear_fecha, formatear_fecha_hora, formatear_moneda


def test_formatear_moneda_usd() -> None:
    assert formatear_moneda(Decimal("1234.56"), Moneda.USD) == "$ 1234.56"


def test_formatear_moneda_bs() -> None:
    assert formatear_moneda(Decimal("999.99"), Moneda.BS) == "Bs 999.99"


def test_formatear_moneda_redondea_half_up() -> None:
    assert formatear_moneda(Decimal("10.005"), Moneda.USD) == "$ 10.01"


def test_formatear_moneda_rechaza_float() -> None:
    with pytest.raises(TypeError):
        formatear_moneda(10.5, Moneda.USD)


def test_formatear_moneda_rechaza_no_moneda() -> None:
    with pytest.raises(ValueError):
        formatear_moneda(Decimal("10"), "USD")


def test_formatear_fecha_desde_date() -> None:
    assert formatear_fecha(date(2026, 9, 9)) == "09/09/2026"


def test_formatear_fecha_desde_datetime() -> None:
    assert formatear_fecha(datetime(2026, 9, 9, 15, 30)) == "09/09/2026"


def test_formatear_fecha_rechaza_str() -> None:
    with pytest.raises(TypeError):
        formatear_fecha("2026-09-09")


def test_formatear_fecha_hora() -> None:
    assert formatear_fecha_hora(datetime(2026, 9, 9, 15, 30)) == "09/09/2026 15:30"


def test_formatear_fecha_hora_rechaza_date() -> None:
    with pytest.raises(TypeError):
        formatear_fecha_hora(date(2026, 9, 9))