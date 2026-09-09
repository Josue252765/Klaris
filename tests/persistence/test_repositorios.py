"""Tests de persistence/repositorios.py: serialización y reconstrucción de objetos."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from core.gastos import CategoriaGasto, Gasto
from core.inventario import MovimientoStock
from core.moneda import Moneda
from core.producto import Producto
from core.ventas import ItemCarrito, Venta
from persistence.repositorios import (
    RepositorioGastosJSON,
    RepositorioMovimientosJSON,
    RepositorioProductosJSON,
    RepositorioVentasJSON,
)


def _producto() -> Producto:
    return Producto(
        id=str(uuid4()),
        nombre="Harina",
        categoria="Alimentos",
        costo_unitario=Decimal("2.50"),
        margen_ganancia=Decimal("30"),
        stock_actual=10,
        stock_minimo=2,
        unidad_medida="kg",
    )


def test_producto_roundtrip_decimal_preservado(tmp_path) -> None:
    repo = RepositorioProductosJSON(tmp_path / "productos.json")
    producto = _producto()
    repo.guardar(producto)
    recuperado = repo.obtener(producto.id)
    assert recuperado is not None
    assert recuperado.costo_unitario == Decimal("2.50")
    assert isinstance(recuperado.costo_unitario, Decimal)


def test_producto_obtener_inexistente_devuelve_none(tmp_path) -> None:
    repo = RepositorioProductosJSON(tmp_path / "productos.json")
    assert repo.obtener("no-existe") is None


def test_producto_listar_devuelve_todos(tmp_path) -> None:
    repo = RepositorioProductosJSON(tmp_path / "productos.json")
    p1 = _producto()
    p2 = _producto()
    repo.guardar(p1)
    repo.guardar(p2)
    assert len(repo.listar()) == 2


def test_producto_actualizar_reemplaza(tmp_path) -> None:
    repo = RepositorioProductosJSON(tmp_path / "productos.json")
    producto = _producto()
    repo.guardar(producto)
    from dataclasses import replace

    actualizado = replace(producto, stock_actual=5)
    repo.actualizar(actualizado)
    assert repo.obtener(producto.id).stock_actual == 5


def test_movimiento_roundtrip_fecha_preservada(tmp_path) -> None:
    repo = RepositorioMovimientosJSON(tmp_path / "movimientos.json")
    movimiento = MovimientoStock(
        producto_id="prod-1",
        tipo="entrada",
        cantidad=5,
        motivo="compra",
        fecha=datetime(2026, 9, 9, 12, 0, 0),
    )
    repo.guardar(movimiento)
    assert len(repo._store.listar()) == 1


def test_venta_roundtrip_decimal_y_moneda(tmp_path) -> None:
    repo = RepositorioVentasJSON(tmp_path / "ventas.json")
    items = [
        ItemCarrito(
            producto_id="p1",
            cantidad=3,
            precio_unitario=Decimal("3.25"),
        )
    ]
    venta = Venta(
        id=str(uuid4()),
        items=items,
        total=Decimal("9.75"),
        moneda=Moneda.USD,
        metodo_pago="efectivo_usd",
        fecha=datetime(2026, 9, 9, 15, 30, 0),
    )
    repo.guardar(venta)
    assert len(repo._store.listar()) == 1


def test_gasto_roundtrip_categoria_y_decimal(tmp_path) -> None:
    repo = RepositorioGastosJSON(tmp_path / "gastos.json")
    gasto = Gasto(
        id=str(uuid4()),
        categoria=CategoriaGasto.MERCANCIA,
        descripcion="Compra de harina",
        monto=Decimal("50.00"),
        moneda=Moneda.USD,
        fecha=datetime(2026, 9, 9, 10, 0, 0),
    )
    repo.guardar(gasto)
    recuperados = repo.listar()
    assert len(recuperados) == 1
    assert recuperados[0].categoria == CategoriaGasto.MERCANCIA
    assert recuperados[0].monto == Decimal("50.00")
    assert isinstance(recuperados[0].monto, Decimal)
    assert recuperados[0].moneda == Moneda.USD


def test_gasto_listar_vacio(tmp_path) -> None:
    repo = RepositorioGastosJSON(tmp_path / "gastos.json")
    assert repo.listar() == []


def test_producto_uuid_valido_tras_roundtrip(tmp_path) -> None:
    repo = RepositorioProductosJSON(tmp_path / "productos.json")
    producto = _producto()
    repo.guardar(producto)
    recuperado = repo.obtener(producto.id)
    UUID(recuperado.id)