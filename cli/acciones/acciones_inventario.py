"""Acciones de CLI relacionadas con Inventario."""

from datetime import date

from core.inventario import GestorInventario, MovimientoStock
from core.producto import GestorProductos
from cli.helpers import buscar_producto, pedir_int, seleccionar_producto
from utils.excepciones import KlarisError
from utils.formatos import formatear_fecha_hora


def accion_entrada_inventario(
    gestor_inventario: GestorInventario, gestor_productos: GestorProductos
) -> None:
    """Registra una entrada de stock pidiendo datos por teclado."""
    try:
        producto = seleccionar_producto(gestor_productos)
        if producto is None:
            return
        cantidad = pedir_int("Cantidad")
        motivo = input("Motivo: ").strip()
        movimiento = gestor_inventario.registrar_entrada(producto.id, cantidad, motivo)
        print(f"OK: entrada registrada (+{movimiento.cantidad})")
    except (KlarisError, ValueError) as e:
        print(f"Error: {e}")


def accion_salida_inventario(
    gestor_inventario: GestorInventario, gestor_productos: GestorProductos
) -> None:
    """Registra una salida de stock pidiendo datos por teclado; notifica si queda stock bajo."""
    try:
        producto = seleccionar_producto(gestor_productos)
        if producto is None:
            return
        cantidad = pedir_int("Cantidad")
        motivo = input("Motivo: ").strip()
        movimiento = gestor_inventario.registrar_salida(producto.id, cantidad, motivo)
        print(f"OK: salida registrada (-{movimiento.cantidad})")
        if gestor_inventario.verificar_stock_bajo(producto.id):
            actualizado = gestor_productos.obtener(producto.id)
            print(
                f"ALERTA: {actualizado.nombre} quedó con stock bajo "
                f"({actualizado.stock_actual}/{actualizado.stock_minimo})."
            )
    except (KlarisError, ValueError) as e:
        print(f"Error: {e}")


def accion_ajustar_stock(
    gestor_inventario: GestorInventario, gestor_productos: GestorProductos
) -> None:
    """Ajusta el stock a un valor exacto pidiendo datos por teclado."""
    try:
        producto = seleccionar_producto(gestor_productos)
        if producto is None:
            return
        nueva_cantidad = pedir_int("Nueva cantidad")
        motivo = input("Motivo: ").strip()
        movimiento = gestor_inventario.ajustar_stock(producto.id, nueva_cantidad, motivo)
        print(f"OK: stock ajustado a {movimiento.cantidad}")
    except (KlarisError, ValueError) as e:
        print(f"Error: {e}")


def accion_ver_stock_bajo(
    gestor_inventario: GestorInventario, gestor_productos: GestorProductos
) -> None:
    """Muestra los productos activos con stock bajo o igual al mínimo."""
    productos = gestor_inventario.listar_productos_bajo_minimo(gestor_productos)
    if not productos:
        print("No hay productos con stock bajo.")
        return
    print("Productos con stock bajo:")
    for p in productos:
        print(f"  [{p.codigo}] {p.nombre} | {p.stock_actual}/{p.stock_minimo}")


def accion_historial_movimientos(
    gestor_inventario: GestorInventario, gestor_productos: GestorProductos
) -> None:
    """Muestra el historial de movimientos de inventario con filtros opcionales."""
    try:
        texto = input("Producto (nombre/código) o Enter para todos: ").strip()
        producto_id = None
        if texto:
            producto = buscar_producto(gestor_productos, texto)
            if producto is None:
                return
            producto_id = producto.id
        desde = _pedir_fecha_opcional("Desde")
        hasta = _pedir_fecha_opcional("Hasta")
        movimientos = gestor_inventario.historial_movimientos(
            producto_id, desde, hasta
        )
        _imprimir_movimientos(movimientos, gestor_productos)
    except (KlarisError, ValueError) as e:
        print(f"Error: {e}")


def _pedir_fecha_opcional(prompt: str) -> date | None:
    texto = input(f"{prompt} (YYYY-MM-DD) o Enter sin filtro: ").strip()
    return date.fromisoformat(texto) if texto else None


def _imprimir_movimientos(
    movimientos: list[MovimientoStock], gestor_productos: GestorProductos
) -> None:
    if not movimientos:
        print("Sin movimientos para los filtros dados.")
        return
    nombres = {p.id: p.nombre for p in gestor_productos.listar(solo_activos=False)}
    print("\n--- HISTORIAL DE MOVIMIENTOS ---")
    for m in movimientos:
        nombre = nombres.get(m.producto_id, m.producto_id[:8])
        print(
            f"  {formatear_fecha_hora(m.fecha)} | {m.tipo:7s} | {nombre} | "
            f"cant: {m.cantidad} | {m.motivo}"
        )
    print("-" * 40)
