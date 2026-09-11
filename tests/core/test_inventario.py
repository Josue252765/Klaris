"""Tests de core/inventario.py: GestorInventario con repositorios en memoria."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from core.inventario import GestorInventario, MovimientoStock
from core.producto import GestorProductos, Producto
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
        codigo="ALI-0001",
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


def test_verificar_stock_bajo(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, repo_prod, _ = gestor
    bajo = _producto(stock=1, stock_minimo=2)
    limite = _producto(stock=2, stock_minimo=2)
    alto = _producto(stock=5, stock_minimo=2)
    repo_prod.guardar(bajo)
    repo_prod.guardar(limite)
    repo_prod.guardar(alto)
    assert g.verificar_stock_bajo(bajo.id) is True
    assert g.verificar_stock_bajo(limite.id) is True
    assert g.verificar_stock_bajo(alto.id) is False


def test_verificar_stock_bajo_producto_no_encontrado(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, _, _ = gestor
    with pytest.raises(ProductoNoEncontradoError):
        g.verificar_stock_bajo("inexistente")


def test_listar_productos_bajo_minimo(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, repo_prod, _ = gestor
    gestor_prod = GestorProductos(repo_prod)
    alto = _producto(stock=20, stock_minimo=2)
    bajo = _producto(stock=1, stock_minimo=2)
    inactivo_bajo = Producto(
        id=str(uuid4()), nombre="Inactivo", categoria="X",
        costo_unitario=Decimal("1.00"), margen_ganancia=Decimal("10"),
        stock_actual=0, stock_minimo=5, unidad_medida="u", codigo="X-0001",
        activo=False,
    )
    repo_prod.guardar(alto)
    repo_prod.guardar(bajo)
    repo_prod.guardar(inactivo_bajo)
    resultado = g.listar_productos_bajo_minimo(gestor_prod)
    assert len(resultado) == 1
    assert resultado[0].id == bajo.id


def test_historial_movimientos_filtros(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, repo_prod, repo_mov = gestor
    p1 = _producto()
    p2 = _producto()
    repo_prod.guardar(p1)
    repo_prod.guardar(p2)

    m1 = MovimientoStock(p1.id, "entrada", 10, "compra", fecha=datetime(2026, 9, 1, 10, 0))
    m2 = MovimientoStock(p1.id, "salida", 2, "venta", fecha=datetime(2026, 9, 5, 12, 0))
    m3 = MovimientoStock(p2.id, "entrada", 5, "compra", fecha=datetime(2026, 9, 10, 15, 0))
    repo_mov.guardar(m1)
    repo_mov.guardar(m2)
    repo_mov.guardar(m3)

    # Sin filtros
    assert len(g.historial_movimientos()) == 3

    # Por producto
    assert len(g.historial_movimientos(producto_id=p1.id)) == 2

    # Por fecha desde/hasta
    rango = g.historial_movimientos(desde=date(2026, 9, 5), hasta=date(2026, 9, 10))
    assert len(rango) == 2
    assert {m.producto_id for m in rango} == {p1.id, p2.id}

    # Combinado
    comb = g.historial_movimientos(producto_id=p1.id, desde=date(2026, 9, 5))
    assert len(comb) == 1
    assert comb[0].motivo == "venta"


def test_movimiento_registra_fecha(
    gestor: tuple[GestorInventario, RepoProductosMemoria, RepoMovimientosMemoria],
) -> None:
    g, repo_prod, _ = gestor
    producto = _producto()
    repo_prod.guardar(producto)
    movimiento = g.registrar_entrada(producto.id, 3, "compra")
    assert movimiento.fecha is not None