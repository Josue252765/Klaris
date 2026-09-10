"""Punto de entrada de Klaris. Menú principal y dispatch a acciones de la CLI."""

from pathlib import Path

from cli.acciones import (
    accion_actualizar_tasa,
    accion_ajustar_stock,
    accion_anular_venta,
    accion_buscar_producto,
    accion_cierre_de_caja,
    accion_crear_producto,
    accion_editar_producto,
    accion_entrada_inventario,
    accion_listar_gastos,
    accion_listar_productos,
    accion_registrar_gasto,
    accion_reporte_dia,
    accion_salida_inventario,
    accion_top_productos,
    accion_ver_stock_bajo,
    accion_ver_tasa,
    accion_vender,
)
from config.settings import Settings
from core.devoluciones import GestorDevoluciones
from core.gastos import GestorGastos
from core.inventario import GestorInventario
from core.producto import GestorProductos
from core.reportes import GeneradorReportes
from core.tasas import GestorTasas
from core.ventas import GestorVentas
from persistence.repositorios import (
    RepositorioAnulacionesJSON,
    RepositorioGastosJSON,
    RepositorioMovimientosJSON,
    RepositorioProductosJSON,
    RepositorioTasaJSON,
    RepositorioVentasJSON,
)

_MENU = """\
=== Klaris ===
1. Productos
2. Inventario
3. Ventas
4. Gastos
5. Tasas de cambio
6. Reporte del día
7. Reportes y cierre de caja
8. Salir
"""


def main() -> None:
    """Instancia gestores y ejecuta el loop del menú principal."""
    config = Settings(directorio_datos=Path("data"))
    repo_productos = RepositorioProductosJSON(config.ruta_productos())
    repo_movimientos = RepositorioMovimientosJSON(config.ruta_movimientos())
    repo_ventas = RepositorioVentasJSON(config.ruta_ventas())
    repo_gastos = RepositorioGastosJSON(config.ruta_gastos())
    repo_tasas = RepositorioTasaJSON(config.ruta_tasas())
    repo_anulaciones = RepositorioAnulacionesJSON(config.ruta_anulaciones())

    gestor_tasas = GestorTasas(repo_tasas)
    gestor_productos = GestorProductos(repo_productos, repo_tasas)
    gestor_inventario = GestorInventario(repo_productos, repo_movimientos)
    gestor_ventas = GestorVentas(
        gestor_inventario, repo_productos, repo_ventas, repo_tasas
    )
    gestor_gastos = GestorGastos(repo_gastos, repo_tasas)
    gestor_devoluciones = GestorDevoluciones(
        gestor_ventas, gestor_inventario, repo_anulaciones
    )
    generador_reportes = GeneradorReportes(gestor_ventas, gestor_gastos, repo_tasas)

    while True:
        print(_MENU)
        opcion = input("Opción: ").strip()
        if opcion == "1":
            _menu_productos(gestor_productos)
        elif opcion == "2":
            _menu_inventario(gestor_inventario, gestor_productos)
        elif opcion == "3":
            _menu_ventas(gestor_ventas, gestor_productos, gestor_devoluciones)
        elif opcion == "4":
            _menu_gastos(gestor_gastos)
        elif opcion == "5":
            _menu_tasas(gestor_tasas)
        elif opcion == "6":
            accion_reporte_dia(gestor_ventas, gestor_gastos)
        elif opcion == "7":
            _menu_reportes(generador_reportes, repo_productos)
        elif opcion == "8":
            print("Hasta luego.")
            break
        else:
            print("Opción inválida.")


def _menu_productos(gestor_productos: GestorProductos) -> None:
    """Submenú de productos: listar, crear, buscar, editar."""
    print("  a) Listar  b) Crear  c) Buscar  d) Editar")
    sub = input("  Opción: ").strip().lower()
    if sub == "a":
        accion_listar_productos(gestor_productos)
    elif sub == "b":
        accion_crear_producto(gestor_productos)
    elif sub == "c":
        accion_buscar_producto(gestor_productos)
    elif sub == "d":
        accion_editar_producto(gestor_productos)


def _menu_inventario(
    gestor_inventario: GestorInventario, gestor_productos: GestorProductos
) -> None:
    """Submenú de inventario: entrada, salida, ajustar, stock bajo."""
    print("  a) Entrada  b) Salida  c) Ajustar  d) Stock bajo")
    sub = input("  Opción: ").strip().lower()
    if sub == "a":
        accion_entrada_inventario(gestor_inventario, gestor_productos)
    elif sub == "b":
        accion_salida_inventario(gestor_inventario, gestor_productos)
    elif sub == "c":
        accion_ajustar_stock(gestor_inventario, gestor_productos)
    elif sub == "d":
        accion_ver_stock_bajo(gestor_inventario)


def _menu_ventas(
    gestor_ventas: GestorVentas,
    gestor_productos: GestorProductos,
    gestor_devoluciones: GestorDevoluciones,
) -> None:
    """Submenú de ventas: vender, anular."""
    print("  a) Vender  b) Anular venta")
    sub = input("  Opción: ").strip().lower()
    if sub == "a":
        accion_vender(gestor_ventas, gestor_productos)
    elif sub == "b":
        accion_anular_venta(gestor_devoluciones, gestor_ventas)


def _menu_gastos(gestor_gastos: GestorGastos) -> None:
    """Submenú de gastos: registrar, listar."""
    print("  a) Registrar  b) Listar")
    sub = input("  Opción: ").strip().lower()
    if sub == "a":
        accion_registrar_gasto(gestor_gastos)
    elif sub == "b":
        accion_listar_gastos(gestor_gastos)


def _menu_tasas(gestor_tasas: GestorTasas) -> None:
    """Submenú de tasas: actualizar, ver."""
    print("  a) Actualizar  b) Ver")
    sub = input("  Opción: ").strip().lower()
    if sub == "a":
        accion_actualizar_tasa(gestor_tasas)
    elif sub == "b":
        accion_ver_tasa(gestor_tasas)


def _menu_reportes(generador: GeneradorReportes, repo_productos) -> None:
    """Submenú de reportes: cierre de caja, top productos."""
    print("  a) Cierre de caja  b) Top productos vendidos")
    sub = input("  Opción: ").strip().lower()
    if sub == "a":
        accion_cierre_de_caja(generador)
    elif sub == "b":
        accion_top_productos(generador, repo_productos)


if __name__ == "__main__":
    main()
