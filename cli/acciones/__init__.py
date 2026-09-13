"""Acciones de la CLI: una función por opción de menú, sin lógica de negocio."""

from cli.acciones.acciones_configuracion import (
    accion_editar_configuracion,
)
from cli.acciones.acciones_clientes import (
    accion_registrar_abono,
    accion_registrar_cliente,
    accion_ver_clientes_deudas,
)
from cli.acciones.acciones_exportacion import (
    accion_crear_backup,
    accion_exportar_catalogo,
    accion_exportar_cierre,
    accion_exportar_cuentas,
    accion_exportar_gastos,
    accion_exportar_movimientos,
    accion_exportar_ventas,
)
from cli.acciones.acciones_gastos import (
    accion_listar_gastos,
    accion_registrar_gasto,
)
from cli.acciones.acciones_inventario import (
    accion_ajustar_stock,
    accion_entrada_inventario,
    accion_historial_movimientos,
    accion_salida_inventario,
    accion_ver_stock_bajo,
)
from cli.acciones.acciones_productos import (
    accion_buscar_producto,
    accion_crear_producto,
    accion_editar_producto,
    accion_listar_productos,
)
from cli.acciones.acciones_reportes import (
    accion_cierre_de_caja,
    accion_reporte_dia,
    accion_top_productos,
)
from cli.acciones.acciones_tasas import (
    accion_actualizar_tasa,
    accion_ver_tasa,
)
from cli.acciones.acciones_ventas import (
    accion_anular_venta,
    accion_vender,
)

__all__ = [
    "accion_editar_configuracion",
    "accion_crear_backup",
    "accion_exportar_catalogo",
    "accion_exportar_cierre",
    "accion_exportar_cuentas",
    "accion_exportar_gastos",
    "accion_exportar_movimientos",
    "accion_exportar_ventas",
    "accion_registrar_abono",
    "accion_registrar_cliente",
    "accion_ver_clientes_deudas",
    "accion_listar_gastos",
    "accion_registrar_gasto",
    "accion_ajustar_stock",
    "accion_entrada_inventario",
    "accion_historial_movimientos",
    "accion_salida_inventario",
    "accion_ver_stock_bajo",
    "accion_buscar_producto",
    "accion_crear_producto",
    "accion_editar_producto",
    "accion_listar_productos",
    "accion_cierre_de_caja",
    "accion_reporte_dia",
    "accion_top_productos",
    "accion_actualizar_tasa",
    "accion_ver_tasa",
    "accion_anular_venta",
    "accion_vender",
]
