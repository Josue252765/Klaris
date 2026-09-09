# Módulo: core/ventas.py

Responsabilidad: carrito temporal, cierre de venta, actualización de stock asociada.

## Clase `ItemCarrito` (`@dataclass`)

| Atributo | Tipo | Nota |
|---|---|---|
| `producto_id` | `str` | — |
| `cantidad` | `int` | > 0 |
| `precio_unitario` | `Decimal` | **snapshot** al momento de agregar — nunca referencia viva al producto |

## Clase `Carrito`

| Firma | Retorna | Lanza |
|---|---|---|
| `agregar_item(producto: Producto, cantidad: int) -> None` | — | valida stock disponible antes de agregar |
| `quitar_item(producto_id: str) -> None` | — | — |
| `total() -> Decimal` | suma de items | — |
| `vaciar() -> None` | — | — |

## Clase `Venta` (`@dataclass`)

| Atributo | Tipo |
|---|---|
| `id` | `str` (UUID4) |
| `items` | `list[ItemCarrito]` |
| `total` | `Decimal` |
| `moneda` | `Moneda` |
| `metodo_pago` | `str` — "efectivo_usd", "efectivo_bs", "pago_movil", "otro" |
| `fecha` | `datetime` |

## Clase `GestorVentas`

`cerrar_venta(carrito: Carrito, moneda: Moneda, metodo_pago: str) -> Venta`

Flujo obligatorio, en este orden exacto:
1. Si carrito vacío → `CarritoVacioError`.
2. Validar disponibilidad de stock de **todos** los items antes de descontar ninguno (simular transacción — si un item falla, no debe quedar stock parcialmente descontado de otro).
3. Por cada item: `GestorInventario.registrar_salida(...)`.
4. Construir y persistir `Venta` vía `VentaRepository`.
5. Devolver la `Venta` cerrada.

Impresión de ticket: texto plano simple en `main.py`. No es un módulo aparte en el MVP.
