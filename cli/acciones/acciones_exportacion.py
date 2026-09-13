"""Acciones CLI para backups y exportaciones CSV."""

from datetime import date
from pathlib import Path
from typing import Callable

from cli.helpers import buscar_producto
from core.clientes import GestorClientes
from core.gastos import CategoriaGasto, GestorGastos
from core.inventario import GestorInventario
from core.producto import GestorProductos
from core.reportes import GeneradorReportes
from core.ventas import GestorVentas
from exportacion import (
    exportar_catalogo_productos,
    exportar_cierre_caja,
    exportar_cuentas_por_cobrar,
    exportar_gastos,
    exportar_movimientos_inventario,
    exportar_ventas,
)
from persistence.backup import crear_backup
from utils.excepciones import KlarisError, ValorInvalidoError

_CATEGORIAS_GASTO = {
    "1": CategoriaGasto.MERCANCIA,
    "2": CategoriaGasto.SERVICIOS,
    "3": CategoriaGasto.SUELDOS,
    "4": CategoriaGasto.OTROS,
}


def accion_crear_backup(directorio_datos: Path) -> None:
    """Crea un backup bajo la carpeta backups y muestra la ruta."""
    _ejecutar(lambda: crear_backup(directorio_datos, Path("backups")), "Backup creado")


def accion_exportar_catalogo(gestor: GestorProductos) -> None:
    """Exporta el catálogo completo de productos."""
    _ejecutar(lambda: exportar_catalogo_productos(gestor), "Catálogo exportado")


def accion_exportar_ventas(gestor: GestorVentas) -> None:
    """Pide un rango opcional y exporta las ventas."""
    try:
        desde, hasta = _pedir_rango()
        _mostrar_ruta(exportar_ventas(gestor, desde, hasta), "Ventas exportadas")
    except (KlarisError, OSError, ValueError) as exc:
        print(f"Error: {exc}")


def accion_exportar_gastos(gestor: GestorGastos) -> None:
    """Pide rango y categoría opcionales y exporta los gastos."""
    try:
        desde, hasta = _pedir_rango()
        categoria = _pedir_categoria_gasto()
        ruta = exportar_gastos(
            gestor, desde, hasta, categoria=categoria
        )
        _mostrar_ruta(ruta, "Gastos exportados")
    except (KlarisError, OSError, ValueError) as exc:
        print(f"Error: {exc}")


def accion_exportar_cierre(gestor: GeneradorReportes) -> None:
    """Pide un rango y exporta el cierre de caja calculado."""
    try:
        desde, hasta = _pedir_rango_cierre()
        _mostrar_ruta(exportar_cierre_caja(gestor, desde, hasta), "Cierre exportado")
    except (KlarisError, OSError, ValueError) as exc:
        print(f"Error: {exc}")


def accion_exportar_cuentas(gestor: GestorClientes) -> None:
    """Exporta las cuentas por cobrar con saldo pendiente."""
    _ejecutar(lambda: exportar_cuentas_por_cobrar(gestor), "Cuentas exportadas")


def accion_exportar_movimientos(
    inventario: GestorInventario, productos: GestorProductos
) -> None:
    """Pide producto y rango opcionales y exporta movimientos de inventario."""
    try:
        texto = input("Producto (nombre/código) o Enter para todos: ").strip()
        producto = buscar_producto(productos, texto) if texto else None
        if texto and producto is None:
            return
        desde, hasta = _pedir_rango()
        producto_id = producto.id if producto is not None else None
        ruta = exportar_movimientos_inventario(
            inventario, producto_id, desde, hasta
        )
        _mostrar_ruta(ruta, "Movimientos exportados")
    except (KlarisError, OSError, ValueError) as exc:
        print(f"Error: {exc}")


def _pedir_rango() -> tuple[date | None, date | None]:
    desde_texto = input("Desde (YYYY-MM-DD) o Enter sin filtro: ").strip()
    hasta_texto = input("Hasta (YYYY-MM-DD) o Enter sin filtro: ").strip()
    desde = date.fromisoformat(desde_texto) if desde_texto else None
    hasta = date.fromisoformat(hasta_texto) if hasta_texto else None
    return desde, hasta


def _pedir_categoria_gasto() -> CategoriaGasto | None:
    print("Categoría: 1=MERCANCIA 2=SERVICIOS 3=SUELDOS 4=OTROS")
    opcion = input("Opción o Enter sin filtro: ").strip()
    if not opcion:
        return None
    if opcion not in _CATEGORIAS_GASTO:
        raise ValorInvalidoError("Categoría inválida.")
    return _CATEGORIAS_GASTO[opcion]


def _pedir_rango_cierre() -> tuple[date, date]:
    desde_texto = input("Desde (YYYY-MM-DD) o Enter para hoy: ").strip()
    desde = date.fromisoformat(desde_texto) if desde_texto else date.today()
    hasta_texto = input("Hasta (YYYY-MM-DD) o Enter = mismo día: ").strip()
    hasta = date.fromisoformat(hasta_texto) if hasta_texto else desde
    return desde, hasta


def _ejecutar(operacion: Callable[[], Path], mensaje: str) -> None:
    try:
        _mostrar_ruta(operacion(), mensaje)
    except (KlarisError, OSError, ValueError) as exc:
        print(f"Error: {exc}")


def _mostrar_ruta(ruta: Path, mensaje: str) -> None:
    print(f"OK: {mensaje}: {ruta}")
