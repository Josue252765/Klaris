"""Tests de cli/acciones.py: ventas, gastos, tasas y reporte."""

from decimal import Decimal
from uuid import uuid4

from cli.acciones import (
    accion_actualizar_tasa,
    accion_anular_venta,
    accion_listar_gastos,
    accion_registrar_gasto,
    accion_reporte_dia,
    accion_ver_tasa,
    accion_vender,
)
from core.configuracion import ConfiguracionNegocio, GestorConfiguracion
from core.devoluciones import GestorDevoluciones
from core.gastos import CategoriaGasto, Gasto, GestorGastos
from core.inventario import GestorInventario
from core.moneda import Moneda
from core.producto import GestorProductos
from core.tasas import GestorTasas
from core.ventas import GestorVentas
from tests.cli.conftest import producto, tasa, RepoGastosMemoria, RepoProductosMemoria, RepoMovimientosMemoria, RepoTasaMemoria, RepoVentasMemoria


class RepoAnulacionesMemoria:
    def __init__(self):
        self._items = []

    def guardar(self, a) -> None:
        self._items.append(a)

    def listar(self) -> list:
        return list(self._items)


class RepoConfiguracionMemoria:
    def __init__(self) -> None:
        self._configuracion: ConfiguracionNegocio | None = None

    def obtener(self) -> ConfiguracionNegocio | None:
        return self._configuracion

    def guardar(self, config: ConfiguracionNegocio) -> None:
        self._configuracion = config


# --- Vender ---


def test_vender_feliz(capsys, monkeypatch) -> None:
    repo_prod = RepoProductosMemoria()
    repo_mov = RepoMovimientosMemoria()
    repo_ventas = RepoVentasMemoria()
    repo_tasa = RepoTasaMemoria()
    p = producto(stock=10)
    repo_prod.guardar(p)
    inventario = GestorInventario(repo_prod, repo_mov)
    gestor = GestorVentas(inventario, repo_prod, repo_ventas, repo_tasa)
    gestor_prod = GestorProductos(repo_prod, repo_tasa)
    inputs = iter(["Harina", "2", "listo", "efectivo_usd", "USD"])
    monkeypatch.setattr("builtins.input", lambda p="": next(inputs))
    accion_vender(
        gestor,
        gestor_prod,
        configuracion=GestorConfiguracion(RepoConfiguracionMemoria()),
    )
    out = capsys.readouterr().out
    assert "TICKET" in out
    assert repo_prod.obtener(p.id).stock_actual == 8


def test_vender_carrito_vacio(capsys, monkeypatch) -> None:
    repo_prod = RepoProductosMemoria()
    inventario = GestorInventario(repo_prod, RepoMovimientosMemoria())
    gestor = GestorVentas(inventario, repo_prod, RepoVentasMemoria(), RepoTasaMemoria())
    gestor_prod = GestorProductos(repo_prod, RepoTasaMemoria())
    monkeypatch.setattr("builtins.input", lambda p="": "listo")
    accion_vender(
        gestor,
        gestor_prod,
        configuracion=GestorConfiguracion(RepoConfiguracionMemoria()),
    )
    assert "Nada que vender" in capsys.readouterr().out


def test_anular_venta_feliz(capsys, monkeypatch) -> None:
    repo_prod = RepoProductosMemoria()
    repo_mov = RepoMovimientosMemoria()
    repo_ventas = RepoVentasMemoria()
    p = producto(stock=10)
    repo_prod.guardar(p)
    inventario = GestorInventario(repo_prod, repo_mov)
    gestor = GestorVentas(inventario, repo_prod, repo_ventas, RepoTasaMemoria())
    gestor_prod = GestorProductos(repo_prod, RepoTasaMemoria())
    inputs_venta = iter(["Harina", "2", "listo", "efectivo_usd", "USD"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs_venta))
    accion_vender(
        gestor,
        gestor_prod,
        configuracion=GestorConfiguracion(RepoConfiguracionMemoria()),
    )
    venta = repo_ventas.listar()[0]
    inputs_anul = iter([venta.id[:8], "error de cobro"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs_anul))
    gestor_dev = GestorDevoluciones(gestor, inventario, RepoAnulacionesMemoria())
    accion_anular_venta(gestor_dev, gestor)
    out = capsys.readouterr().out
    assert "OK: venta anulada" in out
    assert repo_prod.obtener(p.id).stock_actual == 10


def test_anular_venta_sin_ventas(capsys) -> None:
    inventario = GestorInventario(RepoProductosMemoria(), RepoMovimientosMemoria())
    gestor = GestorVentas(
        inventario, RepoProductosMemoria(), RepoVentasMemoria(), RepoTasaMemoria()
    )
    gestor_dev = GestorDevoluciones(gestor, inventario, RepoAnulacionesMemoria())
    accion_anular_venta(gestor_dev, gestor)
    assert "No hay ventas para anular" in capsys.readouterr().out


# --- Gastos ---


def test_registrar_gasto_feliz(capsys, monkeypatch) -> None:
    repo = RepoGastosMemoria()
    gestor = GestorGastos(repo)
    monkeypatch.setattr("builtins.input", lambda p="": {
        "Opción: ": "1", "Descripción: ": "Compra",
        "Monto: ": "50", "Moneda del gasto (USD/BS): ": "USD",
    }.get(p, ""))
    accion_registrar_gasto(gestor)
    assert "OK: gasto" in capsys.readouterr().out
    assert len(repo.listar()) == 1


def test_registrar_gasto_categoria_invalida(capsys, monkeypatch) -> None:
    gestor = GestorGastos(RepoGastosMemoria())
    monkeypatch.setattr("builtins.input", lambda p="": "9")
    accion_registrar_gasto(gestor)
    assert "Error:" in capsys.readouterr().out


def test_listar_gastos_vacio(capsys) -> None:
    accion_listar_gastos(GestorGastos(RepoGastosMemoria()))
    assert "No hay gastos." in capsys.readouterr().out


def test_listar_gastos_con_datos(capsys) -> None:
    repo = RepoGastosMemoria()
    repo.guardar(Gasto(
        id=str(uuid4()), categoria=CategoriaGasto.MERCANCIA,
        descripcion="Harina", monto=Decimal("50"), moneda=Moneda.USD,
    ))
    accion_listar_gastos(GestorGastos(repo))
    assert "Harina" in capsys.readouterr().out


# --- Tasas ---


def test_actualizar_tasa_feliz(capsys, monkeypatch) -> None:
    repo = RepoTasaMemoria()
    gestor = GestorTasas(repo)
    monkeypatch.setattr("builtins.input", lambda p="": {
        "Tasa referencial (Bs por USD): ": "40",
        "Tasa diaria (Bs por USD): ": "42",
    }[p])
    accion_actualizar_tasa(gestor)
    assert "OK: tasa actualizada" in capsys.readouterr().out
    assert repo.obtener_actual() is not None


def test_actualizar_tasa_error(capsys, monkeypatch) -> None:
    gestor = GestorTasas(RepoTasaMemoria())
    monkeypatch.setattr("builtins.input", lambda p="": "abc")
    accion_actualizar_tasa(gestor)
    assert "Error:" in capsys.readouterr().out


def test_ver_tasa_sin_guardar(capsys) -> None:
    accion_ver_tasa(GestorTasas(RepoTasaMemoria()))
    assert "No hay tasa guardada" in capsys.readouterr().out


def test_ver_tasa_guardada(capsys) -> None:
    repo = RepoTasaMemoria()
    repo.guardar(tasa())
    accion_ver_tasa(GestorTasas(repo))
    out = capsys.readouterr().out
    assert "Tasa referencial:" in out
    assert "42" in out


# --- Reporte ---


def test_reporte_dia_vacio(capsys, monkeypatch) -> None:
    repo_tasa = RepoTasaMemoria()
    inventario = GestorInventario(RepoProductosMemoria(), RepoMovimientosMemoria())
    gestor_ventas = GestorVentas(inventario, RepoProductosMemoria(), RepoVentasMemoria(), repo_tasa)
    gestor_gastos = GestorGastos(RepoGastosMemoria(), repo_tasa)
    monkeypatch.setattr("builtins.input", lambda p="": "")
    accion_reporte_dia(gestor_ventas, gestor_gastos)
    out = capsys.readouterr().out
    assert "Ventas (0)" in out
    assert "Ganancia neta" in out


def test_reporte_dia_error_fecha(capsys, monkeypatch) -> None:
    repo_tasa = RepoTasaMemoria()
    inventario = GestorInventario(RepoProductosMemoria(), RepoMovimientosMemoria())
    gestor_ventas = GestorVentas(inventario, RepoProductosMemoria(), RepoVentasMemoria(), repo_tasa)
    gestor_gastos = GestorGastos(RepoGastosMemoria(), repo_tasa)
    monkeypatch.setattr("builtins.input", lambda p="": "no-es-fecha")
    accion_reporte_dia(gestor_ventas, gestor_gastos)
    assert "Error:" in capsys.readouterr().out
