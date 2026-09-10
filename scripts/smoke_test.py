"""Script de prueba de humo: verifica que el motor conecta de extremo a extremo."""

import json
from pathlib import Path

from config.settings import Settings
from core.gastos import CategoriaGasto, GestorGastos
from core.inventario import GestorInventario
from core.moneda import Moneda
from core.producto import GestorProductos
from core.ventas import Carrito, GestorVentas
from decimal import Decimal
from persistence.repositorios import (
    RepositorioGastosJSON,
    RepositorioMovimientosJSON,
    RepositorioProductosJSON,
    RepositorioTasaJSON,
    RepositorioVentasJSON,
)


def main() -> None:
    config = Settings(directorio_datos=Path("data"))

    repo_productos = RepositorioProductosJSON(config.ruta_productos())
    repo_movimientos = RepositorioMovimientosJSON(config.ruta_movimientos())
    repo_ventas = RepositorioVentasJSON(config.ruta_ventas())
    repo_gastos = RepositorioGastosJSON(config.ruta_gastos())
    repo_tasas = RepositorioTasaJSON(config.ruta_tasas())

    gestor_productos = GestorProductos(repo_productos)
    gestor_inventario = GestorInventario(repo_productos, repo_movimientos)
    gestor_ventas = GestorVentas(gestor_inventario, repo_productos, repo_ventas)
    gestor_gastos = GestorGastos(repo_gastos)

    print("=== Prueba de humo de Klaris ===")

    producto = gestor_productos.crear(
        nombre="Harina de maíz",
        categoria="Alimentos",
        costo_unitario=Decimal("2.50"),
        margen_ganancia=Decimal("30"),
        stock_inicial=0,
        stock_minimo=2,
        unidad_medida="kg",
    )
    print(f"OK: producto creado (id={producto.id})")

    movimiento = gestor_inventario.registrar_entrada(
        producto.id, 10, "compra inicial"
    )
    print(f"OK: entrada registrada (+{movimiento.cantidad} unidades)")

    producto_actualizado = repo_productos.obtener(producto.id)
    print(f"OK: stock tras entrada = {producto_actualizado.stock_actual}")

    carrito = Carrito()
    carrito.agregar_item(producto_actualizado, 3)
    venta = gestor_ventas.cerrar_venta(carrito, Moneda.USD, "efectivo_usd")
    print(f"OK: venta registrada (id={venta.id}, total={venta.total})")

    producto_final = repo_productos.obtener(producto.id)
    print(f"OK: stock tras venta = {producto_final.stock_actual} (debe ser 7)")

    gasto = gestor_gastos.registrar(
        CategoriaGasto.MERCANCIA,
        "Compra de harina",
        Decimal("25.00"),
        Moneda.USD,
    )
    print(f"OK: gasto registrado (id={gasto.id}, monto={gasto.monto})")

    with open(config.ruta_ventas(), "r", encoding="utf-8") as f:
        contenido = json.load(f)
    print(f"OK: ventas.json tiene {len(contenido)} registro(s):")
    print(json.dumps(contenido, ensure_ascii=False, indent=2))

    print("=== Fin ===")


if __name__ == "__main__":
    main()
