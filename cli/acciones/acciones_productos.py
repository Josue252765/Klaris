"""Acciones de CLI relacionadas con Productos."""

from decimal import Decimal

from core.moneda import Moneda
from core.producto import GestorProductos
from cli.helpers import (
    pedir_decimal,
    pedir_int,
    pedir_moneda,
    seleccionar_producto,
)
from utils.excepciones import KlarisError
from utils.formatos import formatear_moneda


def accion_crear_producto(gestor: GestorProductos) -> None:
    """Crea un producto pidiendo datos por teclado; imprime confirmación o error."""
    try:
        nombre = input("Nombre: ").strip()
        categoria = input("Categoría: ").strip()
        moneda_costo = pedir_moneda("Moneda del costo")
        costo = pedir_decimal("Costo unitario")
        margen = pedir_decimal("Margen de ganancia (%)")
        stock = pedir_int("Stock inicial")
        stock_min = pedir_int("Stock mínimo")
        unidad = input("Unidad de medida: ").strip()
        producto = gestor.crear(
            nombre=nombre, categoria=categoria, costo_unitario=costo,
            margen_ganancia=margen, stock_inicial=stock,
            stock_minimo=stock_min, unidad_medida=unidad,
            costo_moneda=moneda_costo,
        )
        print(f"OK: producto creado (id={producto.id})")
    except (KlarisError, ValueError, ArithmeticError) as e:
        print(f"Error: {e}")


def accion_listar_productos(gestor: GestorProductos) -> None:
    """Lista todos los productos activos con su stock."""
    productos = gestor.listar()
    if not productos:
        print("No hay productos.")
        return
    for p in productos:
        print(f"  [{p.codigo}] {p.nombre} | {p.categoria} | "
              f"costo {formatear_moneda(p.costo_unitario, Moneda.USD)} | "
              f"stock {p.stock_actual}/{p.stock_minimo} {p.unidad_medida}")


def accion_buscar_producto(gestor: GestorProductos) -> None:
    """Busca productos por nombre y muestra coincidencias."""
    try:
        texto = input("Texto a buscar: ").strip()
        resultados = gestor.buscar_por_nombre(texto)
        if not resultados:
            print("Sin coincidencias.")
            return
        for p in resultados:
            print(f"  [{p.codigo}] {p.nombre} | stock {p.stock_actual}")
    except KlarisError as e:
        print(f"Error: {e}")


def accion_editar_producto(gestor: GestorProductos) -> None:
    """Edita campos de un producto; Enter = mantener valor actual."""
    try:
        producto = seleccionar_producto(gestor)
        if producto is None:
            return
        print(f"Editando: {producto.nombre}")
        campos: dict[str, object] = {}
        costo_moneda = Moneda.USD
        nuevo = input(f"Nombre ({producto.nombre}): ").strip()
        if nuevo:
            campos["nombre"] = nuevo
        nuevo_costo = input(f"Costo unitario ({producto.costo_unitario}): ").strip()
        if nuevo_costo:
            costo_moneda = pedir_moneda("Moneda del nuevo costo")
            campos["costo_unitario"] = Decimal(nuevo_costo)
        nuevo_stock = input(f"Stock actual ({producto.stock_actual}): ").strip()
        if nuevo_stock:
            campos["stock_actual"] = int(nuevo_stock)
        if campos:
            gestor.actualizar(producto.id, costo_moneda=costo_moneda, **campos)
            print("OK: producto actualizado.")
        else:
            print("Sin cambios.")
    except (KlarisError, ValueError, ArithmeticError) as e:
        print(f"Error: {e}")
