# Módulo: core/ventas.py

Responsabilidad: carrito temporal, cierre de venta, actualización de stock asociada.

## Clase `ItemCarrito` (`@dataclass`, `frozen=True`)

| Atributo | Tipo | Nota |
|---|---|---|
| `producto_id` | `str` | — |
| `cantidad` | `int` | > 0 |
| `precio_unitario` | `Decimal` | **snapshot** al momento de agregar — nunca referencia viva al producto |

## Clase `Carrito`

| Firma | Retorna | Lanza |
|---|---|---|
| `agregar_item(producto: Producto, cantidad: int) -> None` | — | `ValorInvalidoError` si cantidad ≤ 0; `StockInsuficienteError` si supera stock disponible |
| `quitar_item(producto_id: str) -> None` | — | — |
| `total() -> Decimal` | suma de items en USD | — |
| `vaciar() -> None` | — | — |
| `esta_vacio() -> bool` | `True` si sin items | — |
| `items() -> list[ItemCarrito]` | copia de la lista interna | — |

`agregar_item` acumula cantidad si el producto ya está en el carrito; el stock disponible se valida contra el total acumulado.

## Clase `Venta` (`@dataclass`, `frozen=True`)

| Atributo | Tipo | Nota |
|---|---|---|
| `id` | `str` (UUID4) | — |
| `items` | `list[ItemCarrito]` | snapshot inmutable |
| `total` | `Decimal` | siempre en USD |
| `moneda` | `Moneda` | moneda de referencia de los precios (`USD`) |
| `metodo_pago` | `str` | `"efectivo_usd"`, `"efectivo_bs"`, `"pago_movil"`, `"otro"` |
| `fecha` | `datetime` | `datetime.now()` al cerrar |
| `total_bs` | `Decimal \| None` | total convertido a BS con tasa diaria; `None` si pago en USD |
| `tasa_usada` | `Decimal \| None` | valor numérico de `tasa_diaria` aplicado; `None` si pago en USD |
| `monto_recibido_bs` | `Decimal \| None` | monto entregado por el cliente en BS; `None` si pago en USD |
| `vuelto_bs` | `Decimal \| None` | `monto_recibido_bs − total_bs`; `None` si pago en USD |
| `anulada` | `bool` | `False` al cerrar; `True` tras `GestorDevoluciones.anular_venta` |

## Clase `GestorVentas`

### `cerrar_venta(carrito, moneda, metodo_pago, moneda_pago=Moneda.USD, monto_recibido_bs=None) -> Venta`

Flujo obligatorio, en este orden exacto:

1. Si carrito vacío → `CarritoVacioError`.
2. Validar `metodo_pago` contra `METODOS_PAGO_VALIDOS` → `ValorInvalidoError` si no pertenece.
3. Validar stock de **todos** los items antes de descontar ninguno (si un item falla, no queda stock parcialmente descontado de otro).
4. Si `moneda_pago == Moneda.BS`: verificar que `monto_recibido_bs` no sea `None` y sea ≥ `total_bs` (calculado con `tasa_diaria` del `RepositorioTasa`). Esta validación ocurre **antes** de descontar stock → `ValorInvalidoError` si insuficiente; `MonedaInvalidaError` si no hay tasa cargada.
5. Por cada item: `GestorInventario.registrar_salida(producto_id, cantidad, "venta")`.
6. Calcular `total_bs`, `tasa_usada` y `vuelto_bs` si `moneda_pago == Moneda.BS`; `None` en los tres si USD.
7. Construir y persistir `Venta` vía `RepositorioVentas`.
8. Devolver la `Venta` cerrada.

### `listar(desde=None, hasta=None) -> list[Venta]`

Devuelve ventas filtrando por rango de fechas (ambos extremos inclusivos). Sin filtro devuelve todas, incluidas las anuladas.

### `obtener(venta_id: str) -> Venta | None`

Busca por id exacto. `None` si no existe.

### `marcar_anulada(venta_id: str) -> Venta`

Persiste `anulada=True` vía `RepositorioVentas.actualizar`. Lanza `ValorInvalidoError` si la venta no existe o ya está anulada. No reingresa stock: eso lo hace `GestorDevoluciones.anular_venta`.

## Flujo CLI (`cli/acciones.py` y `main.py`)

Menú principal opción **3. Ventas**:

| Subopción | Función | Pasos |
|---|---|---|
| a) Vender | `accion_vender` | armar carrito → método de pago → moneda → monto en BS si aplica → `cerrar_venta` → ticket |
| b) Anular venta | `accion_anular_venta` | listar ventas no anuladas → pedir id (prefijo único) y motivo → `GestorDevoluciones.anular_venta` |

`accion_vender`:

1. Armar carrito interactivamente con `armar_carrito` (agrega productos por código/nombre hasta que el usuario indique fin).
2. Pedir método de pago (`pedir_metodo_pago`): muestra las 4 opciones.
3. Pedir moneda de pago (`pedir_moneda`): `USD` o `BS`.
4. Si `moneda_pago == BS`: `pedir_monto_recibido` solicita el monto en BS. Si `USD`, `monto_recibido` es `None`.
5. Llamar a `cerrar_venta` con todos los parámetros.
6. Imprimir ticket (`imprimir_ticket`): items, total USD y, si aplica, total BS, tasa usada y vuelto BS.

## Persistencia (`data/ventas.json`)

Esquema de cada registro:

```json
{
  "id": "str (UUID4)",
  "items": [{"producto_id": "str", "cantidad": 1, "precio_unitario": "str Decimal"}],
  "total": "str Decimal (USD)",
  "moneda": "USD",
  "metodo_pago": "efectivo_bs",
  "fecha": "ISO 8601",
  "total_bs": "str Decimal | null",
  "tasa_usada": "str Decimal | null",
  "monto_recibido_bs": "str Decimal | null",
  "vuelto_bs": "str Decimal | null",
  "anulada": false
}
```

Todos los `Decimal` se serializan como `str`; se reconstruyen con `Decimal(str)` al deserializar — nunca pasan por `float`.
