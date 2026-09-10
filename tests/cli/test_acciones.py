"""Tests de cli/acciones.py: productos, inventario."""

from decimal import Decimal
from uuid import uuid4

from cli.acciones import (
    accion_buscar_producto,
    accion_crear_producto,
    accion_editar_producto,
    accion_entrada_inventario,
    accion_listar_productos,
    accion_salida_inventario,
    accion_ajustar_stock,
    accion_ver_stock_bajo,
)
from core.inventario import GestorInventario
from core.producto import GestorProductos, Producto
from tests.cli.conftest import producto, RepoProductosMemoria, RepoMovimientosMemoria


# --- Crear producto ---


def test_crear_producto_feliz(capsys, monkeypatch) -> None:
    repo = RepoProductosMemoria()
    gestor = GestorProductos(repo)
    monkeypatch.setattr("builtins.input", lambda p="": {
        "Nombre: ": "Aceite", "Categoría: ": "Alimentos",
        "Moneda del costo (USD/BS): ": "USD", "Costo unitario: ": "4.00",
        "Margen de ganancia (%): ": "30", "Stock inicial: ": "5",
        "Stock mínimo: ": "1", "Unidad de medida: ": "litro",
    }[p])
    accion_crear_producto(gestor)
    assert "OK: producto creado" in capsys.readouterr().out
    assert len(repo.listar()) == 1


def test_crear_producto_error(capsys, monkeypatch) -> None:
    gestor = GestorProductos(RepoProductosMemoria())
    monkeypatch.setattr("builtins.input", lambda p="": {
        "Nombre: ": "", "Categoría: ": "x",
    }.get(p, "0"))
    accion_crear_producto(gestor)
    assert "Error:" in capsys.readouterr().out


# --- Listar ---


def test_listar_productos_vacio(capsys) -> None:
    accion_listar_productos(GestorProductos(RepoProductosMemoria()))
    assert "No hay productos." in capsys.readouterr().out


def test_listar_productos_con_datos(capsys) -> None:
    repo = RepoProductosMemoria()
    repo.guardar(producto())
    accion_listar_productos(GestorProductos(repo))
    assert "Harina" in capsys.readouterr().out


# --- Buscar ---


def test_buscar_producto_feliz(capsys, monkeypatch) -> None:
    repo = RepoProductosMemoria()
    repo.guardar(producto())
    monkeypatch.setattr("builtins.input", lambda p="": "har")
    accion_buscar_producto(GestorProductos(repo))
    assert "Harina" in capsys.readouterr().out


def test_buscar_producto_sin_resultado(capsys, monkeypatch) -> None:
    repo = RepoProductosMemoria()
    repo.guardar(producto())
    monkeypatch.setattr("builtins.input", lambda p="": "xyz")
    accion_buscar_producto(GestorProductos(repo))
    assert "Sin coincidencias" in capsys.readouterr().out


# --- Editar ---


def test_editar_producto_feliz(capsys, monkeypatch) -> None:
    repo = RepoProductosMemoria()
    p = producto()
    repo.guardar(p)
    monkeypatch.setattr("builtins.input", lambda prompt="": {
        "Producto (nombre/código): ": "Harina",
        f"Nombre ({p.nombre}): ": "Harina nueva",
        f"Costo unitario ({p.costo_unitario}): ": "",
        f"Stock actual ({p.stock_actual}): ": "",
    }[prompt])
    accion_editar_producto(GestorProductos(repo))
    assert "OK:" in capsys.readouterr().out
    assert repo.obtener(p.id).nombre == "Harina nueva"


def test_editar_producto_costo(capsys, monkeypatch) -> None:
    repo = RepoProductosMemoria()
    p = producto()
    repo.guardar(p)
    monkeypatch.setattr("builtins.input", lambda prompt="": {
        "Producto (nombre/código): ": "Harina",
        f"Nombre ({p.nombre}): ": "",
        f"Costo unitario ({p.costo_unitario}): ": "3.50",
        "Moneda del nuevo costo (USD/BS): ": "USD",
        f"Stock actual ({p.stock_actual}): ": "",
    }[prompt])
    accion_editar_producto(GestorProductos(repo))
    assert "OK: producto actualizado." in capsys.readouterr().out
    assert repo.obtener(p.id).costo_unitario == Decimal("3.50")


def test_editar_producto_no_encontrado(capsys, monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda p="": "inexistente")
    accion_editar_producto(GestorProductos(RepoProductosMemoria()))
    assert "Producto no encontrado" in capsys.readouterr().out


# --- Inventario ---


def test_entrada_inventario_feliz(capsys, monkeypatch) -> None:
    repo_prod = RepoProductosMemoria()
    repo_mov = RepoMovimientosMemoria()
    p = producto(stock=5)
    repo_prod.guardar(p)
    monkeypatch.setattr("builtins.input", lambda prompt="": {
        "Producto (nombre/código): ": "Harina", "Cantidad: ": "3", "Motivo: ": "compra",
    }[prompt])
    accion_entrada_inventario(
        GestorInventario(repo_prod, repo_mov), GestorProductos(repo_prod)
    )
    assert "OK: entrada" in capsys.readouterr().out
    assert repo_prod.obtener(p.id).stock_actual == 8


def test_entrada_inventario_error(capsys, monkeypatch) -> None:
    repo_prod = RepoProductosMemoria()
    repo_mov = RepoMovimientosMemoria()
    monkeypatch.setattr("builtins.input", lambda p="": "inexistente")
    accion_entrada_inventario(
        GestorInventario(repo_prod, repo_mov), GestorProductos(repo_prod)
    )
    assert "Producto no encontrado" in capsys.readouterr().out


def test_salida_inventario_feliz(capsys, monkeypatch) -> None:
    repo_prod = RepoProductosMemoria()
    repo_mov = RepoMovimientosMemoria()
    p = producto(stock=10)
    repo_prod.guardar(p)
    monkeypatch.setattr("builtins.input", lambda prompt="": {
        "Producto (nombre/código): ": "Harina", "Cantidad: ": "2", "Motivo: ": "venta",
    }[prompt])
    accion_salida_inventario(
        GestorInventario(repo_prod, repo_mov), GestorProductos(repo_prod)
    )
    assert "OK: salida" in capsys.readouterr().out
    assert repo_prod.obtener(p.id).stock_actual == 8


def test_salida_inventario_stock_insuficiente(capsys, monkeypatch) -> None:
    repo_prod = RepoProductosMemoria()
    p = producto(stock=1)
    repo_prod.guardar(p)
    monkeypatch.setattr("builtins.input", lambda prompt="": {
        "Producto (nombre/código): ": "Harina", "Cantidad: ": "5", "Motivo: ": "venta",
    }[prompt])
    accion_salida_inventario(
        GestorInventario(repo_prod, RepoMovimientosMemoria()),
        GestorProductos(repo_prod),
    )
    assert "Error:" in capsys.readouterr().out


def test_ajustar_stock_feliz(capsys, monkeypatch) -> None:
    repo_prod = RepoProductosMemoria()
    p = producto(stock=10)
    repo_prod.guardar(p)
    monkeypatch.setattr("builtins.input", lambda prompt="": {
        "Producto (nombre/código): ": "Harina", "Nueva cantidad: ": "20", "Motivo: ": "conteo",
    }[prompt])
    accion_ajustar_stock(
        GestorInventario(repo_prod, RepoMovimientosMemoria()),
        GestorProductos(repo_prod),
    )
    assert "OK: stock ajustado" in capsys.readouterr().out
    assert repo_prod.obtener(p.id).stock_actual == 20


def test_ver_stock_bajo(capsys) -> None:
    repo_prod = RepoProductosMemoria()
    repo_prod.guardar(producto(stock=1))
    accion_ver_stock_bajo(GestorInventario(repo_prod, RepoMovimientosMemoria()))
    assert "Harina" in capsys.readouterr().out
