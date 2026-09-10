# Módulo: core/reportes.py

Responsabilidad: consolidar ventas y gastos en reportes de solo lectura (cierre de caja y ranking de productos). No genera PDF ni Excel.

## Clase `DesglosePago` (`@dataclass`, `frozen=True`)

| Atributo | Tipo | Nota |
|---|---|---|
| `metodo` | `str` | `"efectivo_usd"`, `"efectivo_bs"`, `"pago_movil"` u `"otro"` |
| `total_usd` | `Decimal` | suma de `Venta.total` de ese método |
| `cantidad_ventas` | `int` | número de ventas del método |

## Clase `CierreCaja` (`@dataclass`, `frozen=True`)

| Atributo | Tipo | Nota |
|---|---|---|
| `fecha_desde` | `date` | inicio del período (inclusive) |
| `fecha_hasta` | `date` | fin del período (inclusive) |
| `total_ventas_usd` | `Decimal` | suma de ventas del período |
| `total_ventas_bs` | `Decimal` | `total_ventas_usd * tasa_diaria`; `0` si no hay tasa |
| `desglose_pago` | `list[DesglosePago]` | siempre 4 entradas, una por método (aunque el total sea 0) |
| `total_gastos_usd` | `Decimal` | `GestorGastos.total_periodo` del mismo rango |
| `total_gastos_bs` | `Decimal` | `total_gastos_usd * tasa_diaria`; `0` si no hay tasa |
| `balance_neto_usd` | `Decimal` | `total_ventas_usd - total_gastos_usd` (puede ser negativo) |

## Clase `ProductoRanking` (`@dataclass`, `frozen=True`)

| Atributo | Tipo | Nota |
|---|---|---|
| `producto_id` | `str` | id del producto |
| `cantidad_total` | `int` | unidades vendidas acumuladas |
| `monto_total_usd` | `Decimal` | `precio_unitario * cantidad` acumulado (snapshot de cada venta) |

## Clase `GeneradorReportes`

Recibe `gestor_ventas: GestorVentas`, `gestor_gastos: GestorGastos` y opcionalmente `repo_tasa: RepositorioTasa | None`.

Las ventas con `anulada=True` no entran en el cierre de caja ni en el ranking.

### `cierre_de_caja(fecha_desde: date, fecha_hasta: date | None = None) -> CierreCaja`

Si `fecha_hasta` es `None`, el período es un solo día (`fecha_desde`).

1. Listar ventas del rango (extremos inclusivos) y descartar las anuladas.
2. Sumar `Venta.total` → `total_ventas_usd`.
3. Convertir a BS con `tasa_diaria` vigente (`ROUND_HALF_UP`, 2 decimales). Sin tasa o sin `repo_tasa` → `Decimal("0")`.
4. Acumular desglose por `metodo_pago` (los cuatro métodos, aunque alguno quede en cero).
5. `total_gastos_usd` vía `GestorGastos.total_periodo`.
6. Convertir gastos a BS con la misma regla que ventas.
7. `balance_neto_usd = total_ventas_usd - total_gastos_usd`.

No lanza por período vacío: ceros y desglose con cantidades 0.

### `top_productos_vendidos(limite: int = 5, desde: date | None = None, hasta: date | None = None) -> list[ProductoRanking]`

Acumula cantidad y monto por `producto_id` en las ventas no anuladas del rango (sin fechas = todas). Ordena por `cantidad_total` descendente y recorta a `limite`. Sin ventas → lista vacía.

## Flujo CLI (`cli/acciones.py` y `main.py`)

Menú principal opción **7. Reportes y cierre de caja**:

| Subopción | Función | Pasos |
|---|---|---|
| a) Cierre de caja | `accion_cierre_de_caja` | pedir fecha (Enter = hoy) y hasta (Enter = mismo día) → imprimir ventas, desglose con cantidad > 0, gastos y balance neto |
| b) Top productos | `accion_top_productos` | pedir límite (Enter = 5) y rango opcional → imprimir ranking con nombre del producto si existe en el repositorio |

La opción **6. Reporte del día** (`accion_reporte_dia`) es un resumen simple de ventas/gastos; no usa `GeneradorReportes`.

## Dependencias

`core/ventas.py`, `core/gastos.py`, `core/moneda.py` (`RepositorioTasa` para equivalentes en BS). Solo lectura: no persiste ni modifica inventario.
