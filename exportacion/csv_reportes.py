"""Exportación de reportes operativos al formato CSV."""

import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from core.clientes import GestorClientes
from core.gastos import CategoriaGasto, GestorGastos
from core.inventario import GestorInventario
from core.precios import CalculadoraPrecios
from core.producto import GestorProductos
from core.reportes import GeneradorReportes
from core.ventas import GestorVentas, ItemCarrito


def exportar_catalogo_productos(
    gestor_productos: GestorProductos,
    directorio: Path = Path("exports"),
) -> Path:
    """Exporta el catálogo completo de productos y devuelve la ruta del CSV."""
    filas = []
    for producto in gestor_productos.listar(solo_activos=False):
        precio = CalculadoraPrecios.precio_venta(
            producto.costo_unitario, producto.margen_ganancia
        )
        filas.append({
            "nombre": producto.nombre,
            "categoria": producto.categoria,
            "costo": str(producto.costo_unitario),
            "precio_venta": str(precio),
            "stock_actual": producto.stock_actual,
            "stock_minimo": producto.stock_minimo,
            "activo": str(producto.activo),
        })
    campos = (
        "nombre", "categoria", "costo", "precio_venta",
        "stock_actual", "stock_minimo", "activo",
    )
    return _escribir_csv("catalogo_productos", campos, filas, directorio)


def exportar_ventas(
    gestor_ventas: GestorVentas,
    desde: date | None,
    hasta: date | None,
    directorio: Path = Path("exports"),
) -> Path:
    """Exporta las ventas del rango y devuelve la ruta del CSV."""
    filas = [
        {
            "fecha": venta.fecha.isoformat(),
            "items": _resumir_items(venta.items),
            "total_usd": str(venta.total),
            "total_bs": "" if venta.total_bs is None else str(venta.total_bs),
            "metodo_pago": venta.metodo_pago,
            "anulada": str(venta.anulada),
        }
        for venta in gestor_ventas.listar(desde=desde, hasta=hasta)
    ]
    campos = ("fecha", "items", "total_usd", "total_bs", "metodo_pago", "anulada")
    return _escribir_csv("ventas", campos, filas, directorio)


def exportar_gastos(
    gestor_gastos: GestorGastos,
    desde: date | None,
    hasta: date | None,
    directorio: Path = Path("exports"),
    categoria: CategoriaGasto | None = None,
) -> Path:
    """Exporta los gastos del rango y categoría opcional; devuelve su CSV."""
    filas = []
    for gasto in gestor_gastos.listar(
        desde=desde, hasta=hasta, categoria=categoria
    ):
        filas.append({
            "fecha": gasto.fecha.isoformat(),
            "categoria": gasto.categoria.value,
            "descripcion": gasto.descripcion,
            "monto_usd": str(gasto.monto),
            "monto_original": _decimal_opcional(gasto.monto_original),
            "moneda_original": (
                gasto.moneda_original.value if gasto.moneda_original else ""
            ),
            "tasa_usada": _decimal_opcional(gasto.tasa_usada),
        })
    campos = (
        "fecha", "categoria", "descripcion", "monto_usd",
        "monto_original", "moneda_original", "tasa_usada",
    )
    return _escribir_csv("gastos", campos, filas, directorio)


def exportar_cierre_caja(
    gestor_reportes: GeneradorReportes,
    desde: date,
    hasta: date,
    directorio: Path = Path("exports"),
) -> Path:
    """Exporta el cierre calculado por GeneradorReportes y devuelve su CSV."""
    cierre = gestor_reportes.cierre_de_caja(desde, hasta)
    desglose = "; ".join(
        f"{item.metodo}:{item.total_usd}:{item.cantidad_ventas}"
        for item in cierre.desglose_pago
    )
    fila = {
        "fecha_desde": cierre.fecha_desde.isoformat(),
        "fecha_hasta": cierre.fecha_hasta.isoformat(),
        "total_ventas_usd": str(cierre.total_ventas_usd),
        "total_ventas_bs": str(cierre.total_ventas_bs),
        "total_gastos_usd": str(cierre.total_gastos_usd),
        "total_gastos_bs": str(cierre.total_gastos_bs),
        "balance_neto_usd": str(cierre.balance_neto_usd),
        "desglose_pago": desglose,
    }
    campos = tuple(fila.keys())
    return _escribir_csv("cierre_caja", campos, [fila], directorio)


def exportar_cuentas_por_cobrar(
    gestor_clientes: GestorClientes,
    directorio: Path = Path("exports"),
) -> Path:
    """Exporta los saldos pendientes por cliente a la fecha de corte."""
    fecha_corte = date.today().isoformat()
    filas = []
    for cliente in gestor_clientes.listar_clientes():
        saldo = gestor_clientes.obtener_saldo_deuda(cliente.id)
        if saldo > 0:
            filas.append({
                "cliente": cliente.nombre,
                "monto_adeudado": str(saldo),
                "fecha_corte": fecha_corte,
            })
    campos = ("cliente", "monto_adeudado", "fecha_corte")
    return _escribir_csv("cuentas_por_cobrar", campos, filas, directorio)


def exportar_movimientos_inventario(
    gestor_inventario: GestorInventario,
    producto_id: str | None,
    desde: date | None,
    hasta: date | None,
    directorio: Path = Path("exports"),
) -> Path:
    """Exporta el historial filtrado de movimientos y devuelve su CSV."""
    movimientos = gestor_inventario.historial_movimientos(
        producto_id=producto_id, desde=desde, hasta=hasta
    )
    filas = [
        {
            "fecha": movimiento.fecha.isoformat(),
            "producto_id": movimiento.producto_id,
            "tipo": movimiento.tipo,
            "cantidad": movimiento.cantidad,
            "motivo": movimiento.motivo,
        }
        for movimiento in movimientos
    ]
    campos = ("fecha", "producto_id", "tipo", "cantidad", "motivo")
    return _escribir_csv("movimientos_inventario", campos, filas, directorio)


def _resumir_items(items: list[ItemCarrito]) -> str:
    return "; ".join(
        f"{item.producto_id} x{item.cantidad} @ {item.precio_unitario}"
        for item in items
    )


def _decimal_opcional(valor: Decimal | None) -> str:
    return "" if valor is None else str(valor)


def _escribir_csv(
    nombre: str,
    campos: tuple[str, ...],
    filas: Iterable[dict[str, object]],
    directorio: Path,
) -> Path:
    directorio.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    ruta = directorio / f"{nombre}_{timestamp}.csv"
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)
    return ruta
