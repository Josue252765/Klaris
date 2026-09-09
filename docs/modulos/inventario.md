# Módulo: core/inventario.py

Responsabilidad: control de stock, entradas/salidas/ajustes, alertas de stock bajo. Único punto de entrada para modificar `stock_actual` de un `Producto`.

## Clase `MovimientoStock` (`@dataclass`)

| Atributo | Tipo |
|---|---|
| `producto_id` | `str` |
| `tipo` | `Literal["entrada", "salida", "ajuste"]` |
| `cantidad` | `int` |
| `motivo` | `str` |
| `fecha` | `datetime` |

## Clase `GestorInventario`

| Firma | Retorna | Lanza |
|---|---|---|
| `registrar_entrada(producto_id, cantidad, motivo) -> MovimientoStock` | movimiento | `ProductoNoEncontradoError` |
| `registrar_salida(producto_id, cantidad, motivo) -> MovimientoStock` | movimiento | `StockInsuficienteError` si `cantidad > stock_actual`; `ProductoNoEncontradoError` |
| `ajustar_stock(producto_id, nueva_cantidad, motivo) -> MovimientoStock` | movimiento | `ProductoNoEncontradoError`, `ValorInvalidoError` si `nueva_cantidad < 0` |
| `productos_stock_bajo() -> list[Producto]` | productos donde `stock_actual <= stock_minimo` | — |

## Reglas

- `ventas.py` NUNCA decrementa `stock_actual` directamente — siempre llama a `registrar_salida`.
- Todo movimiento se persiste (trazabilidad/auditoría de inventario) vía su propio repositorio.
