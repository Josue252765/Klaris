# Módulo: core/inventario.py

Responsabilidad: control de stock, entradas/salidas/ajustes, alertas de stock bajo. Único punto de entrada para modificar `stock_actual` de un `Producto`.

## Clase `MovimientoStock` (`@dataclass`, `frozen=True`)

| Atributo | Tipo | Nota |
|---|---|---|
| `producto_id` | `str` | — |
| `tipo` | `Literal["entrada", "salida", "ajuste"]` | — |
| `cantidad` | `int` | para ajuste: valor final absoluto, no diferencia |
| `motivo` | `str` | texto libre |
| `fecha` | `datetime` | `datetime.now()` al registrar |

## Clase `GestorInventario`

Recibe `productos: RepositorioProductos` y `movimientos: RepositorioMovimientos` por constructor.

| Firma | Retorna | Lanza |
|---|---|---|
| `registrar_entrada(producto_id, cantidad, motivo) -> MovimientoStock` | movimiento | `ProductoNoEncontradoError`; `ValorInvalidoError` si cantidad ≤ 0 |
| `registrar_salida(producto_id, cantidad, motivo) -> MovimientoStock` | movimiento | `ProductoNoEncontradoError`; `ValorInvalidoError` si cantidad ≤ 0; `StockInsuficienteError` si `cantidad > stock_actual` |
| `ajustar_stock(producto_id, nueva_cantidad, motivo) -> MovimientoStock` | movimiento | `ValorInvalidoError` si `nueva_cantidad < 0`; `ProductoNoEncontradoError` |
| `verificar_stock_bajo(producto_id) -> bool` | `True` si `stock_actual <= stock_minimo` | `ProductoNoEncontradoError` |
| `listar_productos_bajo_minimo(gestor_productos) -> list[Producto]` | productos activos con `stock_actual <= stock_minimo` | — |
| `historial_movimientos(producto_id=None, desde=None, hasta=None) -> list[MovimientoStock]` | lista de movimientos filtrados por producto y/o rango de fechas | — |

`ajustar_stock` fija el stock al valor exacto indicado — no es una entrada ni salida relativa. El movimiento persiste con `tipo="ajuste"` y `cantidad=nueva_cantidad`.

## Flujo CLI (`cli/acciones.py`)

Todas las operaciones de inventario seleccionan el producto primero con `seleccionar_producto(gestor_productos)` (busca por código o nombre).

| Acción | Función CLI | Pasos |
|---|---|---|
| Entrada de stock | `accion_entrada_inventario` | seleccionar producto → pedir cantidad → pedir motivo → `registrar_entrada` |
| Salida de stock | `accion_salida_inventario` | seleccionar producto → pedir cantidad → pedir motivo → `registrar_salida` → si stock bajo, muestra ALERTA |
| Ajuste de stock | `accion_ajustar_stock` | seleccionar producto → pedir nueva cantidad → pedir motivo → `ajustar_stock` |
| Ver stock bajo | `accion_ver_stock_bajo` | llama a `listar_productos_bajo_minimo` y lista `[codigo] nombre \| stock_actual/stock_minimo` |
| Historial movimientos | `accion_historial_movimientos` | producto opcional → rango fecha opcional → llama a `historial_movimientos` y lista registros |

## Reglas

- `ventas.py` NUNCA decrementa `stock_actual` directamente — siempre llama a `registrar_salida`.
- Todo movimiento se persiste en `data/movimientos_stock.json` (trazabilidad/auditoría).
- `GestorProductos.actualizar` no es llamado directamente desde `cli/inventario`; el gestor de inventario actualiza el stock a través del `RepositorioProductos` inyectado.

## Persistencia (`data/movimientos_stock.json`)

```json
{
  "producto_id": "str (UUID4)",
  "tipo": "entrada | salida | ajuste",
  "cantidad": 10,
  "motivo": "str",
  "fecha": "ISO 8601"
}
```
