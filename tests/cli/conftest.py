"""Fixtures compartidas para tests de la CLI."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from core.gastos import Gasto
from core.inventario import MovimientoStock
from core.moneda import TasaCambio
from core.producto import Producto


class RepoProductosMemoria:
    def __init__(self):
        self._datos: dict[str, Producto] = {}

    def guardar(self, p: Producto) -> None:
        self._datos[p.id] = p

    def obtener(self, id: str) -> Producto | None:
        return self._datos.get(id)

    def listar(self) -> list[Producto]:
        return list(self._datos.values())

    def actualizar(self, p: Producto) -> None:
        self._datos[p.id] = p


class RepoMovimientosMemoria:
    def __init__(self):
        self._movs: list[MovimientoStock] = []

    def guardar(self, m: MovimientoStock) -> None:
        self._movs.append(m)

    def listar(self) -> list[MovimientoStock]:
        return list(self._movs)


class RepoVentasMemoria:
    def __init__(self):
        self._ventas: list = []

    def guardar(self, v) -> None:
        self._ventas.append(v)

    def listar(self) -> list:
        return list(self._ventas)


class RepoGastosMemoria:
    def __init__(self):
        self._gastos: list[Gasto] = []

    def guardar(self, g: Gasto) -> None:
        self._gastos.append(g)

    def listar(self) -> list[Gasto]:
        return list(self._gastos)


class RepoTasaMemoria:
    def __init__(self):
        self._tasa: TasaCambio | None = None

    def obtener_actual(self) -> TasaCambio | None:
        return self._tasa

    def guardar(self, t: TasaCambio) -> None:
        self._tasa = t


def producto(stock: int = 10) -> Producto:
    return Producto(
        id=str(uuid4()),
        nombre="Harina",
        categoria="Alimentos",
        costo_unitario=Decimal("2.50"),
        margen_ganancia=Decimal("30"),
        stock_actual=stock,
        stock_minimo=2,
        unidad_medida="kg",
        codigo="ALI-0001",
    )


def tasa() -> TasaCambio:
    return TasaCambio(
        tasa_referencial=Decimal("40"),
        tasa_referencial_fecha=date(2026, 9, 9),
        tasa_diaria=Decimal("42"),
        tasa_diaria_fecha=date(2026, 9, 9),
    )


@pytest.fixture()
def repo_prod():
    return RepoProductosMemoria()


@pytest.fixture()
def repo_mov():
    return RepoMovimientosMemoria()


@pytest.fixture()
def repo_ventas():
    return RepoVentasMemoria()


@pytest.fixture()
def repo_gastos():
    return RepoGastosMemoria()


@pytest.fixture()
def repo_tasa():
    return RepoTasaMemoria()
