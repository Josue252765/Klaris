"""Tests de core/ventas.py: Carrito y GestorVentas con repositorios en memoria."""

from dataclasses import replace
from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest

from core.inventario import GestorInventario, MovimientoStock
from core.moneda import Moneda, TasaCambio
from core.precios import CalculadoraPrecios
from core.producto import Producto
from core.ventas import Carrito, GestorVentas, ItemCarrito, Venta
from utils.excepciones import (
    CarritoVacioError,
    MonedaInvalidaError,
    StockInsuficienteError,
    ValorInvalidoError,
)


class RepoProductosMemoria:
    def __init__(self) -> None:
        self._datos: dict[str, Producto] = {}

    def guardar(self, producto: Producto) -> None:
        self._datos[producto.id] = producto

    def obtener(self, id: str) -> Producto | None:
        return self._datos.get(id)

    def listar(self) -> list[Producto]:
        return list(self._datos.values())

    def actualizar(self, producto: Producto) -> None:
        self._datos[producto.id] = producto


class RepoMovimientosMemoria:
    def __init__(self) -> None:
        self._movimientos: list[MovimientoStock] = []

    def guardar(self, movimiento: MovimientoStock) -> None:
        self._movimientos.append(movimiento)

    def listar(self) -> list[MovimientoStock]:
        return list(self._movimientos)


class RepoVentasMemoria:
    def __init__(self) -> None:
        self._ventas: list[Venta] = []

    def guardar(self, venta: Venta) -> None:
        self._ventas.append(venta)

    def listar(self) -> list[Venta]:
        return list(self._ventas)


def _producto(
    costo: str = "2.50",
    margen: str = "30",
    stock: int = 10,
    stock_minimo: int = 2,
) -> Producto:
    from uuid import uuid4

    return Producto(
        id=str(uuid4()),
        nombre="Harina",
        categoria="Alimentos",
        costo_unitario=Decimal(costo),
        margen_ganancia=Decimal(margen),
        stock_actual=stock,
        stock_minimo=stock_minimo,
        unidad_medida="kg",
        codigo="ALI-0001",
    )


@pytest.fixture()
def infra() -> tuple[GestorVentas, RepoProductosMemoria, RepoVentasMemoria, GestorInventario]:
    repo_prod = RepoProductosMemoria()
    repo_mov = RepoMovimientosMemoria()
    repo_ventas = RepoVentasMemoria()
    inventario = GestorInventario(repo_prod, repo_mov)
    gestor = GestorVentas(inventario, repo_prod, repo_ventas)
    return gestor, repo_prod, repo_ventas, inventario


# --- Carrito ---


def test_carrito_agregar_item_snapshot_precio() -> None:
    producto = _producto(costo="2.50", margen="30")
    carrito = Carrito()
    carrito.agregar_item(producto, 3)
    items = carrito.items()
    assert len(items) == 1
    assert items[0].cantidad == 3
    assert items[0].precio_unitario == Decimal("3.25")


def test_carrito_agregar_mismo_producto_acumula() -> None:
    producto = _producto(stock=10)
    carrito = Carrito()
    carrito.agregar_item(producto, 3)
    carrito.agregar_item(producto, 2)
    assert len(carrito.items()) == 1
    assert carrito.items()[0].cantidad == 5


def test_carrito_total_suma_items() -> None:
    p1 = _producto(costo="2.50", margen="30", stock=10)
    p2 = _producto(costo="1.00", margen="50", stock=10)
    carrito = Carrito()
    carrito.agregar_item(p1, 2)
    carrito.agregar_item(p2, 3)
    assert carrito.total() == Decimal("3.25") * 2 + Decimal("1.50") * 3


def test_carrito_quitar_item() -> None:
    producto = _producto()
    carrito = Carrito()
    carrito.agregar_item(producto, 3)
    carrito.quitar_item(producto.id)
    assert carrito.esta_vacio()


def test_carrito_vaciar() -> None:
    p1 = _producto()
    p2 = _producto()
    carrito = Carrito()
    carrito.agregar_item(p1, 1)
    carrito.agregar_item(p2, 1)
    carrito.vaciar()
    assert carrito.esta_vacio()


def test_carrito_agregar_cantidad_cero_lanza() -> None:
    producto = _producto()
    carrito = Carrito()
    with pytest.raises(ValorInvalidoError):
        carrito.agregar_item(producto, 0)


def test_carrito_agregar_stock_insuficiente_lanza() -> None:
    producto = _producto(stock=3)
    carrito = Carrito()
    with pytest.raises(StockInsuficienteError):
        carrito.agregar_item(producto, 5)


def test_carrito_agregar_acumulado_excede_stock_lanza() -> None:
    producto = _producto(stock=5)
    carrito = Carrito()
    carrito.agregar_item(producto, 3)
    with pytest.raises(StockInsuficienteError):
        carrito.agregar_item(producto, 3)


# --- GestorVentas ---


def test_cerrar_venta_exitosa(
    infra: tuple[GestorVentas, RepoProductosMemoria, RepoVentasMemoria, GestorInventario],
) -> None:
    gestor, repo_prod, repo_ventas, _ = infra
    producto = _producto(costo="2.50", margen="30", stock=10)
    repo_prod.guardar(producto)
    carrito = Carrito()
    carrito.agregar_item(producto, 3)
    venta = gestor.cerrar_venta(carrito, Moneda.USD, "efectivo_usd")
    UUID(venta.id)
    assert venta.total == Decimal("3.25") * 3
    assert venta.moneda == Moneda.USD
    assert venta.metodo_pago == "efectivo_usd"
    assert len(venta.items) == 1
    assert repo_prod.obtener(producto.id).stock_actual == 7
    assert len(repo_ventas.listar()) == 1


def test_cerrar_venta_carrito_vacio_lanza(
    infra: tuple[GestorVentas, RepoProductosMemoria, RepoVentasMemoria, GestorInventario],
) -> None:
    gestor, _, _, _ = infra
    with pytest.raises(CarritoVacioError):
        gestor.cerrar_venta(Carrito(), Moneda.USD, "efectivo_usd")


def test_cerrar_venta_metodo_pago_invalido(
    infra: tuple[GestorVentas, RepoProductosMemoria, RepoVentasMemoria, GestorInventario],
) -> None:
    gestor, repo_prod, _, _ = infra
    producto = _producto()
    repo_prod.guardar(producto)
    carrito = Carrito()
    carrito.agregar_item(producto, 1)
    with pytest.raises(ValorInvalidoError):
        gestor.cerrar_venta(carrito, Moneda.USD, "cripto")


def test_cerrar_venta_stock_insuficiente_no_descuenta(
    infra: tuple[GestorVentas, RepoProductosMemoria, RepoVentasMemoria, GestorInventario],
) -> None:
    gestor, repo_prod, repo_ventas, _ = infra
    p1 = _producto(costo="2.50", margen="30", stock=5)
    p2 = _producto(costo="1.00", margen="50", stock=5)
    repo_prod.guardar(p1)
    repo_prod.guardar(p2)
    carrito = Carrito()
    carrito.agregar_item(p1, 3)
    carrito.agregar_item(p2, 3)
    repo_prod.actualizar(replace(p2, stock_actual=1))
    with pytest.raises(StockInsuficienteError):
        gestor.cerrar_venta(carrito, Moneda.USD, "efectivo_usd")
    assert repo_prod.obtener(p1.id).stock_actual == 5
    assert repo_prod.obtener(p2.id).stock_actual == 1
    assert len(repo_ventas.listar()) == 0


def test_cerrar_venta_multiples_items_descuenta_todos(
    infra: tuple[GestorVentas, RepoProductosMemoria, RepoVentasMemoria, GestorInventario],
) -> None:
    gestor, repo_prod, _, _ = infra
    p1 = _producto(costo="2.50", margen="30", stock=10)
    p2 = _producto(costo="1.00", margen="50", stock=10)
    repo_prod.guardar(p1)
    repo_prod.guardar(p2)
    carrito = Carrito()
    carrito.agregar_item(p1, 2)
    carrito.agregar_item(p2, 3)
    gestor.cerrar_venta(carrito, Moneda.BS, "pago_movil")
    assert repo_prod.obtener(p1.id).stock_actual == 8
    assert repo_prod.obtener(p2.id).stock_actual == 7


def test_cerrar_venta_fecha_se_genera(
    infra: tuple[GestorVentas, RepoProductosMemoria, RepoVentasMemoria, GestorInventario],
) -> None:
    gestor, repo_prod, _, _ = infra
    producto = _producto()
    repo_prod.guardar(producto)
    carrito = Carrito()
    carrito.agregar_item(producto, 1)
    venta = gestor.cerrar_venta(carrito, Moneda.USD, "efectivo_usd")
    assert venta.fecha is not None


# --- Pago en BS (TAREA 2) ---


class RepoTasaMemoria:
    def __init__(self, tasa: TasaCambio | None = None) -> None:
        self._tasa = tasa

    def obtener_actual(self) -> TasaCambio | None:
        return self._tasa


def _tasa_diaria_42() -> TasaCambio:
    return TasaCambio(
        tasa_referencial=Decimal("40"),
        tasa_referencial_fecha=date(2026, 9, 9),
        tasa_diaria=Decimal("42"),
        tasa_diaria_fecha=date(2026, 9, 9),
    )


def test_cerrar_venta_bs_calcula_total_y_vuelto() -> None:
    repo_prod = RepoProductosMemoria()
    repo_mov = RepoMovimientosMemoria()
    repo_ventas = RepoVentasMemoria()
    repo_tasa = RepoTasaMemoria(_tasa_diaria_42())
    inventario = GestorInventario(repo_prod, repo_mov)
    gestor = GestorVentas(inventario, repo_prod, repo_ventas, repo_tasa)
    producto = _producto(costo="2.50", margen="30", stock=10)
    repo_prod.guardar(producto)
    carrito = Carrito()
    carrito.agregar_item(producto, 3)
    venta = gestor.cerrar_venta(
        carrito, Moneda.USD, "efectivo_bs",
        moneda_pago=Moneda.BS, monto_recibido_bs=Decimal("500"),
    )
    assert venta.total == Decimal("9.75")
    assert venta.total_bs == Decimal("409.50")
    assert venta.tasa_usada == Decimal("42")
    assert venta.monto_recibido_bs == Decimal("500")
    assert venta.vuelto_bs == Decimal("90.50")


def test_cerrar_venta_bs_pago_insuficiente_lanza() -> None:
    repo_prod = RepoProductosMemoria()
    repo_mov = RepoMovimientosMemoria()
    repo_ventas = RepoVentasMemoria()
    repo_tasa = RepoTasaMemoria(_tasa_diaria_42())
    inventario = GestorInventario(repo_prod, repo_mov)
    gestor = GestorVentas(inventario, repo_prod, repo_ventas, repo_tasa)
    producto = _producto(costo="2.50", margen="30", stock=10)
    repo_prod.guardar(producto)
    carrito = Carrito()
    carrito.agregar_item(producto, 3)
    with pytest.raises(ValorInvalidoError):
        gestor.cerrar_venta(
            carrito, Moneda.USD, "efectivo_bs",
            moneda_pago=Moneda.BS, monto_recibido_bs=Decimal("100"),
        )


def test_cerrar_venta_bs_monto_recibido_none_lanza() -> None:
    repo_prod = RepoProductosMemoria()
    repo_mov = RepoMovimientosMemoria()
    repo_ventas = RepoVentasMemoria()
    repo_tasa = RepoTasaMemoria(_tasa_diaria_42())
    inventario = GestorInventario(repo_prod, repo_mov)
    gestor = GestorVentas(inventario, repo_prod, repo_ventas, repo_tasa)
    producto = _producto(costo="2.50", margen="30", stock=10)
    repo_prod.guardar(producto)
    carrito = Carrito()
    carrito.agregar_item(producto, 1)
    with pytest.raises(ValorInvalidoError):
        gestor.cerrar_venta(
            carrito, Moneda.USD, "efectivo_bs",
            moneda_pago=Moneda.BS, monto_recibido_bs=None,
        )


def test_cerrar_venta_usd_no_toca_campos_bs() -> None:
    repo_prod = RepoProductosMemoria()
    repo_mov = RepoMovimientosMemoria()
    repo_ventas = RepoVentasMemoria()
    repo_tasa = RepoTasaMemoria(_tasa_diaria_42())
    inventario = GestorInventario(repo_prod, repo_mov)
    gestor = GestorVentas(inventario, repo_prod, repo_ventas, repo_tasa)
    producto = _producto(costo="2.50", margen="30", stock=10)
    repo_prod.guardar(producto)
    carrito = Carrito()
    carrito.agregar_item(producto, 1)
    venta = gestor.cerrar_venta(carrito, Moneda.USD, "efectivo_usd")
    assert venta.total_bs is None
    assert venta.tasa_usada is None
    assert venta.monto_recibido_bs is None
    assert venta.vuelto_bs is None