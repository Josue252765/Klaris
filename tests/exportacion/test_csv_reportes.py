"""Tests roundtrip de las exportaciones CSV."""

import csv
from datetime import date, datetime
from decimal import Decimal

import pytest

from cli.acciones import acciones_exportacion
from core.clientes import Cliente, GestorClientes
from core.gastos import CategoriaGasto, Gasto, GestorGastos
from core.inventario import GestorInventario, MovimientoStock
from core.moneda import Moneda
from core.producto import GestorProductos, Producto
from core.reportes import GeneradorReportes
from core.ventas import GestorVentas, ItemCarrito, Venta
from exportacion import (
    exportar_catalogo_productos,
    exportar_cierre_caja,
    exportar_cuentas_por_cobrar,
    exportar_gastos,
    exportar_movimientos_inventario,
    exportar_ventas,
)


class RepoProductosMemoria:
    def __init__(self) -> None:
        self.datos: dict[str, Producto] = {}

    def guardar(self, producto: Producto) -> None:
        self.datos[producto.id] = producto

    def obtener(self, producto_id: str) -> Producto | None:
        return self.datos.get(producto_id)

    def listar(self) -> list[Producto]:
        return list(self.datos.values())

    def actualizar(self, producto: Producto) -> None:
        self.datos[producto.id] = producto


class RepoListaMemoria:
    def __init__(self) -> None:
        self.datos = []

    def guardar(self, dato) -> None:
        self.datos.append(dato)

    def listar(self) -> list:
        return list(self.datos)

    def actualizar(self, dato) -> None:
        for indice, actual in enumerate(self.datos):
            if actual.id == dato.id:
                self.datos[indice] = dato
                return


class RepoClientesMemoria:
    def __init__(self) -> None:
        self.datos: dict[str, Cliente] = {}

    def guardar(self, cliente: Cliente) -> None:
        self.datos[cliente.id] = cliente

    def obtener(self, cliente_id: str) -> Cliente | None:
        return self.datos.get(cliente_id)

    def listar(self) -> list[Cliente]:
        return list(self.datos.values())


def _producto(activo: bool = True) -> Producto:
    return Producto(
        id="p1",
        nombre="Café molido",
        categoria="Alimentos",
        costo_unitario=Decimal("2.50"),
        margen_ganancia=Decimal("20"),
        stock_actual=8,
        stock_minimo=2,
        unidad_medida="unidad",
        codigo="ALI-0001",
        activo=activo,
    )


def _venta(cliente_id: str | None = None) -> Venta:
    return Venta(
        id="v1",
        items=[ItemCarrito("p1", 2, Decimal("3.00"))],
        total=Decimal("6.00"),
        moneda=Moneda.USD,
        metodo_pago="credito" if cliente_id else "efectivo_bs",
        fecha=datetime(2026, 9, 13, 10, 30),
        total_bs=None if cliente_id else Decimal("240.00"),
        cliente_id=cliente_id,
    )


def _gasto_trazable() -> Gasto:
    return Gasto(
        id="g1",
        categoria=CategoriaGasto.SERVICIOS,
        descripcion="Internet",
        monto=Decimal("12.50"),
        moneda=Moneda.USD,
        fecha=datetime(2026, 9, 13, 9, 0),
        monto_original=Decimal("500.00"),
        moneda_original=Moneda.BS,
        tasa_usada=Decimal("40.00"),
    )


def _leer_csv(ruta) -> list[dict[str, str]]:
    with ruta.open("r", encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def _gestores():
    productos = RepoProductosMemoria()
    movimientos = RepoListaMemoria()
    ventas = RepoListaMemoria()
    gastos = RepoListaMemoria()
    inventario = GestorInventario(productos, movimientos)
    gestor_ventas = GestorVentas(inventario, productos, ventas)
    gestor_gastos = GestorGastos(gastos)
    return (
        productos,
        movimientos,
        ventas,
        gastos,
        inventario,
        gestor_ventas,
        gestor_gastos,
    )


def test_exportar_catalogo_productos_roundtrip(tmp_path) -> None:
    repo = RepoProductosMemoria()
    repo.guardar(_producto(activo=False))

    ruta = exportar_catalogo_productos(GestorProductos(repo), tmp_path)
    filas = _leer_csv(ruta)

    assert filas == [{
        "nombre": "Café molido",
        "categoria": "Alimentos",
        "costo": "2.50",
        "precio_venta": "3.00",
        "stock_actual": "8",
        "stock_minimo": "2",
        "activo": "False",
    }]


def test_exportar_ventas_roundtrip_y_filtra_fecha(tmp_path) -> None:
    _, _, ventas, _, _, gestor_ventas, _ = _gestores()
    ventas.guardar(_venta())

    ruta = exportar_ventas(
        gestor_ventas, date(2026, 9, 13), date(2026, 9, 13), tmp_path
    )
    fila = _leer_csv(ruta)[0]

    assert fila["fecha"] == "2026-09-13T10:30:00"
    assert fila["items"] == "p1 x2 @ 3.00"
    assert fila["total_usd"] == "6.00"
    assert fila["total_bs"] == "240.00"
    assert fila["metodo_pago"] == "efectivo_bs"
    assert fila["anulada"] == "False"


def test_exportar_gastos_roundtrip_filtra_categoria_y_conserva_trazabilidad(
    tmp_path,
) -> None:
    _, _, _, gastos, _, _, gestor_gastos = _gestores()
    gastos.guardar(_gasto_trazable())
    gastos.guardar(Gasto(
        id="g2",
        categoria=CategoriaGasto.OTROS,
        descripcion="Bolsas",
        monto=Decimal("1.00"),
        moneda=Moneda.USD,
        fecha=datetime(2026, 9, 13, 10, 0),
    ))

    ruta = exportar_gastos(
        gestor_gastos, None, None, tmp_path,
        categoria=CategoriaGasto.SERVICIOS,
    )

    assert _leer_csv(ruta) == [{
        "fecha": "2026-09-13T09:00:00",
        "categoria": "SERVICIOS",
        "descripcion": "Internet",
        "monto_usd": "12.50",
        "monto_original": "500.00",
        "moneda_original": "BS",
        "tasa_usada": "40.00",
    }]


@pytest.mark.parametrize(
    ("opcion", "esperada"),
    [("", None), ("2", CategoriaGasto.SERVICIOS)],
)
def test_accion_exportar_gastos_pide_categoria_opcional(
    tmp_path, monkeypatch, opcion, esperada
) -> None:
    recibida = []

    def exportar_falso(gestor, desde, hasta, categoria=None):
        recibida.append(categoria)
        return tmp_path / "gastos.csv"

    entradas = iter(["", "", opcion])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(entradas))
    monkeypatch.setattr(acciones_exportacion, "exportar_gastos", exportar_falso)

    acciones_exportacion.accion_exportar_gastos(object())

    assert recibida == [esperada]


def test_exportar_cierre_caja_roundtrip_reusa_reporte(tmp_path) -> None:
    _, _, ventas, gastos, _, gestor_ventas, gestor_gastos = _gestores()
    ventas.guardar(_venta())
    gastos.guardar(Gasto(
        id="g1",
        categoria=CategoriaGasto.OTROS,
        descripcion="Bolsas",
        monto=Decimal("1.50"),
        moneda=Moneda.USD,
        fecha=datetime(2026, 9, 13, 8, 0),
    ))
    reportes = GeneradorReportes(gestor_ventas, gestor_gastos)

    ruta = exportar_cierre_caja(
        reportes, date(2026, 9, 13), date(2026, 9, 13), tmp_path
    )
    fila = _leer_csv(ruta)[0]

    assert fila["total_ventas_usd"] == "6.00"
    assert fila["total_gastos_usd"] == "1.50"
    assert fila["balance_neto_usd"] == "4.50"
    assert "efectivo_bs:6.00:1" in fila["desglose_pago"]


def test_exportar_cuentas_por_cobrar_roundtrip(tmp_path) -> None:
    productos, _, ventas, _, _, gestor_ventas, _ = _gestores()
    productos.guardar(_producto())
    clientes = RepoClientesMemoria()
    clientes.guardar(Cliente("c1", "Ana Pérez", "V-1", "0414"))
    ventas.guardar(_venta(cliente_id="c1"))
    gestor = GestorClientes(clientes, RepoListaMemoria(), gestor_ventas)

    ruta = exportar_cuentas_por_cobrar(gestor, tmp_path)
    fila = _leer_csv(ruta)[0]

    assert fila["cliente"] == "Ana Pérez"
    assert fila["monto_adeudado"] == "6.00"
    assert fila["fecha_corte"] == date.today().isoformat()


def test_exportar_movimientos_inventario_roundtrip_y_filtra(tmp_path) -> None:
    _, movimientos, _, _, inventario, _, _ = _gestores()
    movimientos.guardar(MovimientoStock(
        producto_id="p1",
        tipo="entrada",
        cantidad=5,
        motivo="Compra inicial",
        fecha=datetime(2026, 9, 13, 8, 30),
    ))
    movimientos.guardar(MovimientoStock(
        producto_id="p2",
        tipo="salida",
        cantidad=1,
        motivo="Venta",
        fecha=datetime(2026, 9, 13, 9, 0),
    ))

    ruta = exportar_movimientos_inventario(
        inventario, "p1", date(2026, 9, 13), date(2026, 9, 13), tmp_path
    )

    assert _leer_csv(ruta) == [{
        "fecha": "2026-09-13T08:30:00",
        "producto_id": "p1",
        "tipo": "entrada",
        "cantidad": "5",
        "motivo": "Compra inicial",
    }]
