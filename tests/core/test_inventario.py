"""Tests de core/inventario.py: GestorInventario con repositorios en memoria."""

from decimal import Decimal
from uuid import uuid4

import pytest

from core.inventario import GestorInventario, MovimientoStock
from core.producto import Producto
from utils.excepciones import (
    ProductoNoEncontradoError,
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


def _producto(stock: int = 10, stock_minimo: int = 2) -> Producto:
    return Producto(
        id=str(uuid4()),
        nombre="Harina",
        categoria="Alimentos",
        costo_unitario=Decimal("2.50"),
        margen_ganancia=Decimal("30"),
        stock_actual=stock,
        stock_minimo=stock_minimo,
        unidad_medida="kg",
    )


@pytest.fixture()
def gestor() -> tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria]:
    repo_prod = RepoProductosMemoria()
    repo_mov = RepoMovimientosMemoria()
    gestor = GestorInventario(repo_prod, repo_mov)
    return gestor, repo_prod, repo_mov


def test_registrar_entrada_incrementa_stock(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, repo_prod, repo_mov = gestor
    producto = _producto(stock=10)
    repo_prod.guardar(producto)
    movimiento = g.registrar_entrada(producto.id, 5, "compra")
    assert repo_prod.obtener(producto.id).stock_actual == 15
    assert movimiento.tipo == "entrada"
    assert movimiento.cantidad == 5
    assert len(repo_mov.listar()) == 1


def test_registrar_entrada_producto_no_encontrado(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, _, _ = gestor
    with pytest.raises(ProductoNoEncontradoError):
        g.registrar_entrada("inexistente", 5, "compra")


def test_registrar_entrada_cantidad_cero_lanza(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, repo_prod, _ = gestor
    producto = _producto()
    repo_prod.guardar(producto)
    with pytest.raises(ValorInvalidoError):
        g.registrar_entrada(producto.id, 0, "compra")


def test_registrar_salida_decrementa_stock(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, repo_prod, repo_mov = gestor
    producto = _producto(stock=10)
    repo_prod.guardar(producto)
    movimiento = g.registrar_salida(producto.id, 4, "venta")
    assert repo_prod.obtener(producto.id).stock_actual == 6
    assert movimiento.tipo == "salida"
    assert len(repo_mov.listar()) == 1


def test_registrar_salida_stock_insuficiente(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, repo_prod, repo_mov = gestor
    producto = _producto(stock=3)
    repo_prod.guardar(producto)
    with pytest.raises(StockInsuficienteError):
        g.registrar_salida(producto.id, 5, "venta")
    assert repo_prod.obtener(producto.id).stock_actual == 3
    assert len(repo_mov.listar()) == 0


def test_registrar_salida_producto_no_encontrado(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, _, _ = gestor
    with pytest.raises(ProductoNoEncontradoError):
        g.registrar_salida("inexistente", 1, "venta")


def test_ajustar_stock_cambia_valor(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, repo_prod, _ = gestor
    producto = _producto(stock=10)
    repo_prod.guardar(producto)
    g.ajustar_stock(producto.id, 20, "conteo")
    assert repo_prod.obtener(producto.id).stock_actual == 20


def test_ajustar_stock_negativo_lanza(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, repo_prod, _ = gestor
    producto = _producto()
    repo_prod.guardar(producto)
    with pytest.raises(ValorInvalidoError):
        g.ajustar_stock(producto.id, -1, "conteo")


def test_ajustar_stock_producto_no_encontrado(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, _, _ = gestor
    with pytest.raises(ProductoNoEncontradoError):
        g.ajustar_stock("inexistente", 5, "conteo")


def test_productos_stock_bajo(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, repo_prod, _ = gestor
    alto = _producto(stock=20, stock_minimo=2)
    bajo = _producto(stock=1, stock_minimo=2)
    en_el_limite = _producto(stock=2, stock_minimo=2)
    repo_prod.guardar(alto)
    repo_prod.guardar(bajo)
    repo_prod.guardar(en_el_limite)
    resultado = g.productos_stock_bajo()
    assert len(resultado) == 2
    assert {p.id for p in resultado} == {bajo.id, en_el_limite.id}


def test_movimiento_registra_fecha(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, repo_prod, _ = gestor
    producto = _producto()
    repo_prod.guardar(producto)
    movimiento = g.registrar_entrada(producto.id, 3, "compra")
    assert movimiento.fecha is not None