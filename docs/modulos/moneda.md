# Módulo: core/moneda.py

Responsabilidad: manejo dual Bs/USD. USD es la moneda base interna para todo cálculo/almacenamiento. Bs es vista derivada de la tasa vigente.

## Clase `Moneda` (Enum)

| Valor | `value` |
|---|---|
| `USD` | `"USD"` |
| `BS` | `"BS"` |

## Clase `TasaCambio` (`@dataclass`, `frozen=True`)

Gestiona dos tasas independientes con fechas de actualización separadas. **Nunca se mezclan**: cada tasa tiene un uso exclusivo.

| Atributo | Tipo | Uso exclusivo |
|---|---|---|
| `tasa_referencial` | `Decimal` (Bs por 1 USD) | **SOLO** para convertir el `costo_unitario` de BS a USD al crear/editar un `Producto` (`GestorProductos`) |
| `tasa_referencial_fecha` | `date` | fecha de actualización de la referencial |
| `tasa_diaria` | `Decimal` (Bs por 1 USD) | **SOLO** para conversión de montos de cobro/vuelto en ventas y registro de gastos en BS |
| `tasa_diaria_fecha` | `date` | fecha de actualización de la diaria |

Ambas tasas se validan en `__post_init__`: deben ser `Decimal` estrictamente positivos → `ValorInvalidoError`.

## Funciones de conversión

### `TasaCambio.convertir(monto, origen, destino, usar) -> Decimal`

| Parámetro | Tipo | Descripción |
|---|---|---|
| `monto` | `Decimal` | monto a convertir |
| `origen` | `Moneda` | moneda de origen |
| `destino` | `Moneda` | moneda de destino |
| `usar` | `Literal["referencial", "diaria"]` | qué tasa aplicar |

**Retorna** el monto convertido, redondeado a 2 decimales con `ROUND_HALF_UP`.

**Lanza:**
- `MonedaInvalidaError` si `origen == destino`.
- `MonedaInvalidaError` si la tasa indicada no está cargada (`None`).

**Fórmulas:**
- `USD → BS`: `monto * tasa`
- `BS → USD`: `monto / tasa`

## Reglas

- Las tasas se actualizan manualmente por el usuario vía `accion_actualizar_tasa` en el CLI. No hay integración con API externa en el MVP.
- Ambas tasas representan Bs por 1 USD.
- `convertir` con `usar="referencial"` usa `tasa_referencial`; con `usar="diaria"` usa `tasa_diaria`. El llamador debe especificar cuál — no hay valor por defecto.
- Si `origen == destino` → `MonedaInvalidaError`.

## Persistencia (`data/tasas.json`)

`TasaCambio` se persiste vía `RepositorioTasaJSON` (`persistence/repositorios.py`). Modelo de **registro único** (no historial en el MVP): `guardar` sobrescribe el único registro; `obtener_actual` lo devuelve o `None` si no hay.

Esquema JSON:

```json
{
  "id": "tasa_actual",
  "tasa_referencial": "str Decimal",
  "tasa_referencial_fecha": "YYYY-MM-DD",
  "tasa_diaria": "str Decimal",
  "tasa_diaria_fecha": "YYYY-MM-DD"
}
```

El campo `id` es siempre `"tasa_actual"` (clave fija del registro único). Los valores `Decimal` se serializan como `str` y se reconstruyen con `Decimal(str)` al leer.

## `RepositorioTasa` (Protocol)

```python
def obtener_actual(self) -> TasaCambio | None: ...
```

Implementado por `RepositorioTasaJSON`. Solo expone `obtener_actual`; `guardar` es responsabilidad del gestor de tasas (`core/tasas.py → GestorTasas`).
