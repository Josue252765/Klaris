"""Tests de cli/acciones/acciones_configuracion.py y helpers imprimir_ticket."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from cli.acciones import accion_editar_configuracion
from cli.helpers import imprimir_ticket
from core.configuracion import ConfiguracionNegocio, GestorConfiguracion
from core.inventario import GestorInventario
from core.moneda import Moneda
from core.producto import GestorProductos
from core.ventas import ItemCarrito, Venta
from tests.cli.conftest import producto, RepoProductosMemoria, RepoMovimientosMemoria


class RepoConfiguracionMemoria:
    def __init__(self) -> None:
        self._configuracion: ConfiguracionNegocio | None = None

    def obtener(self) -> ConfiguracionNegocio | None:
        return self._configuracion

    def guardar(self, config: ConfiguracionNegocio) -> None:
        self._configuracion = config


def test_imprimir_ticket_refleja_nombre_y_pie_configurados(capsys) -> None:
    repo_prod = RepoProductosMemoria()
    p = producto()
    repo_prod.guardar(p)
    gestor_prod = GestorProductos(repo_prod)
    configuracion = ConfiguracionNegocio(
        nombre_negocio="Mi Botica",
        mensaje_pie="¡Gracias por su preferencia!",
        moneda_default=Moneda.USD,
    )
    venta = Venta(
        id="123",
        items=[
            ItemCarrito(
                producto_id=p.id,
                cantidad=1,
                precio_unitario=Decimal("10.00"),
            )
        ],
        total=Decimal("10.00"),
        moneda=Moneda.USD,
        metodo_pago="efectivo_usd",
        fecha=datetime(2026, 9, 13, 12, 0),
        total_bs=None,
        tasa_usada=None,
        monto_recibido_bs=None,
        vuelto_bs=None,
        anulada=False,
        cliente_id=None,
    )
    imprimir_ticket(venta, gestor_prod, configuracion)
    out = capsys.readouterr().out
    assert "Mi Botica" in out
    assert "¡Gracias por su preferencia!" in out


def test_accion_editar_configuracion_feliz(capsys, monkeypatch) -> None:
    repo = RepoConfiguracionMemoria()
    repo.guardar(ConfiguracionNegocio(
        nombre_negocio="Negocio viejo",
        mensaje_pie="Pie viejo",
        moneda_default=Moneda.USD,
    ))
    gestor = GestorConfiguracion(repo)
    inputs = iter([
        "Negocio nuevo", "Pie nuevo", "BS",
    ])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    accion_editar_configuracion(gestor)
    out = capsys.readouterr().out
    assert "OK: configuración actualizada" in out
    config = repo.obtener()
    assert config.nombre_negocio == "Negocio nuevo"
    assert config.mensaje_pie == "Pie nuevo"
    assert config.moneda_default == Moneda.BS


def test_accion_editar_configuracion_mantiene_valor_al_ingresar_vacio(capsys, monkeypatch) -> None:
    repo = RepoConfiguracionMemoria()
    repo.guardar(ConfiguracionNegocio(
        nombre_negocio="Negocio actual",
        mensaje_pie="Mensaje actual",
        moneda_default=Moneda.BS,
    ))
    gestor = GestorConfiguracion(repo)
    inputs = iter(["", "", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    accion_editar_configuracion(gestor)
    out = capsys.readouterr().out
    assert "OK: configuración actualizada" in out
    config = repo.obtener()
    assert config.nombre_negocio == "Negocio actual"
    assert config.mensaje_pie == "Mensaje actual"
    assert config.moneda_default == Moneda.BS
