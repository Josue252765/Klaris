"""Tests de core/devoluciones.py: anulación, stock y exclusión en reportes."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from core.devoluciones import AnulacionVenta, GestorDevoluciones
from core.gastos import GestorGastos
from core.inventario import GestorInventario, MovimientoStock
from core.moneda import Moneda
from core.producto import Producto
from core.reportes import GeneradorReportes
from core.ventas import Carrito, GestorVentas, Venta
from utils.excepciones import ValorInvalidoError


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
        self._items: list[MovimientoStock] = []

    def guardar(self, movimiento: MovimientoStock) -> None:
        self._items.append(movimiento)

    def listar(self) -> list[MovimientoStock]:
        return list(self._items)


class RepoVentasMemoria:
    def __init__(self) -> None:
        self._items: list[Venta] = []

    def guardar(self, venta: Venta) -> None:
        self._items.append(venta)

    def listar(self) -> list[Venta]:
        return list(self._items)

    def actualizar(self, venta: Venta) -> None:
        for i, actual in enumerate(self._items):
            if actual.id == venta.id:
                self._items[i] = venta
                return


class RepoAnulacionesMemoria:
    def __init__(self) -> None:
        self._items: list[AnulacionVenta] = []

    def guardar(self, anulacion: AnulacionVenta) -> None:
        self._items.append(anulacion)

    def listar(self) -> list[AnulacionVenta]:
        return list(self._items)


class RepoGastosMemoria:
    def __init__(self) -> None:
        self._items = []

    def guardar(self, gasto) -> None:
        self._items.append(gasto)

    def listar(self) -> list:
        return list(self._items)


def _producto(stock: int = 10) -> Producto:
    return Producto(
        id=str(uuid4()),
        nombre="Harina",
        categoria="Alimentos",
        costo_unitario=Decimal("2.50"),
        margen_ganancia=Decimal("20"),
        stock_actual=stock,
        stock_minimo=2,
        unidad_medida="kg",
        codigo="ALI-0001",
    )


def _infra():
    repo_prod = RepoProductosMemoria()
    repo_mov = RepoMovimientosMemoria()
    repo_ventas = RepoVentasMemoria()
    repo_anul = RepoAnulacionesMemoria()
    inventario = GestorInventario(repo_prod, repo_mov)
    gestor_ventas = GestorVentas(inventario, repo_prod, repo_ventas)
    gestor_dev = GestorDevoluciones(gestor_ventas, inventario, repo_anul)
    return repo_prod, repo_mov, repo_ventas, repo_anul, gestor_ventas, gestor_dev


def _cerrar_venta(gestor_ventas: GestorVentas, producto: Producto, cantidad: int) -> Venta:
    carrito = Carrito()
    carrito.agregar_item(producto, cantidad)
    return gestor_ventas.cerrar_venta(carrito, Moneda.USD, "efectivo_usd")


def test_anular_venta_exitosa():
    repo_prod, _, _, repo_anul, gestor_ventas, gestor_dev = _infra()
    producto = _producto(stock=10)
    repo_prod.guardar(producto)
    venta = _cerrar_venta(gestor_ventas, producto, 2)

    anulacion = gestor_dev.anular_venta(venta.id, "cliente se arrepintió")

    assert anulacion.venta_id == venta.id
    assert anulacion.motivo == "cliente se arrepintió"
    assert anulacion.monto_devuelto_usd == venta.total
    assert gestor_ventas.obtener(venta.id).anulada is True
    assert len(repo_anul.listar()) == 1


def test_anular_venta_reingresa_stock():
    repo_prod, repo_mov, _, _, gestor_ventas, gestor_dev = _infra()
    producto = _producto(stock=10)
    repo_prod.guardar(producto)
    venta = _cerrar_venta(gestor_ventas, producto, 3)
    assert repo_prod.obtener(producto.id).stock_actual == 7

    gestor_dev.anular_venta(venta.id, "devolución")

    assert repo_prod.obtener(producto.id).stock_actual == 10
    entradas = [m for m in repo_mov.listar() if m.tipo == "entrada"]
    assert len(entradas) == 1
    assert entradas[0].cantidad == 3
    assert venta.id in entradas[0].motivo


def test_anular_venta_previene_doble_anulacion():
    repo_prod, _, _, _, gestor_ventas, gestor_dev = _infra()
    producto = _producto(stock=10)
    repo_prod.guardar(producto)
    venta = _cerrar_venta(gestor_ventas, producto, 1)
    gestor_dev.anular_venta(venta.id, "error de cobro")

    with pytest.raises(ValorInvalidoError, match="ya está anulada"):
        gestor_dev.anular_venta(venta.id, "otro motivo")


def test_anular_venta_inexistente():
    _, _, _, _, _, gestor_dev = _infra()
    with pytest.raises(ValorInvalidoError, match="No existe una venta"):
        gestor_dev.anular_venta("id-falso", "motivo")


def test_anular_venta_motivo_vacio():
    repo_prod, _, _, _, gestor_ventas, gestor_dev = _infra()
    producto = _producto(stock=10)
    repo_prod.guardar(producto)
    venta = _cerrar_venta(gestor_ventas, producto, 1)
    with pytest.raises(ValorInvalidoError, match="motivo"):
        gestor_dev.anular_venta(venta.id, "   ")


def test_reportes_excluyen_ventas_anuladas():
    repo_prod, _, _, repo_anul, gestor_ventas, gestor_dev = _infra()
    producto = _producto(stock=20)
    repo_prod.guardar(producto)
    venta_ok = _cerrar_venta(gestor_ventas, repo_prod.obtener(producto.id), 1)
    venta_anulada = _cerrar_venta(gestor_ventas, repo_prod.obtener(producto.id), 2)
    gestor_dev.anular_venta(venta_anulada.id, "prueba")

    gestor_gastos = GestorGastos(RepoGastosMemoria())
    gen = GeneradorReportes(gestor_ventas, gestor_gastos)
    cierre = gen.cierre_de_caja(date.today())
    ranking = gen.top_productos_vendidos()

    assert cierre.total_ventas_usd == venta_ok.total
    assert ranking[0].cantidad_total == 1
    assert len(repo_anul.listar()) == 1
