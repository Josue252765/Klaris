# Módulo: core/moneda.py

Responsabilidad: manejo dual Bs/USD. USD es la moneda base interna para todo cálculo/almacenamiento. Bs es vista derivada de la tasa vigente.

## Clase `Moneda` (Enum)

| Valor | Tipo |
|---|---|
| `USD` | str |
| `BS` | str |

## Clase `TasaCambio`

Gestiona dos tasas independientes con fechas de actualización separadas. **Nunca se mezclan**: cada tasa tiene un uso exclusivo.

| Atributo | Tipo | Uso exclusivo |
|---|---|---|
| `tasa_referencial` | `Decimal` (Bs por 1 USD) | **SOLO** para fijar `precio_venta` al crear/editar un `Producto` (`precios.py`) |
| `tasa_referencial_fecha` | `date` | fecha de actualización de la referencial |
| `tasa_diaria` | `Decimal` (Bs por 1 USD) | **SOLO** para conversión de montos de cobro/vuelto en `ventas.py` |
| `tasa_diaria_fecha` | `date` | fecha de actualización de la diaria |

## Métodos

| Firma | Retorna | Lanza |
|---|---|---|
| `TasaCambio.convertir(monto: Decimal, origen: Moneda, destino: Moneda, usar: Literal["referencial", "diaria"]) -> Decimal` | monto convertido | `MonedaInvalidaError` si `origen == destino` o si la tasa seleccionada no está cargada |

## Reglas

- Las tasas se actualizan manualmente por el usuario (config). No hay integración con API externa de tasa en el MVP.
- Ambas tasas representan Bs por 1 USD, nunca al revés.
- `tasa_referencial` y `tasa_diaria` son valores independientes: pueden diferir y actualizarse en fechas distintas.
- `convertir` con `usar="referencial"` usa `tasa_referencial`; con `usar="diaria"` usa `tasa_diaria`. No hay valor por defecto: el llamador debe especificar cuál.
- Si `origen == destino`, lanzar `MonedaInvalidaError` (no tiene sentido convertir a la misma moneda).
- Si la tasa seleccionada no está cargada (es `None` o la fecha es `None`), lanzar `MonedaInvalidaError`.

## Persistencia

`TasaCambio` se persiste en su propio archivo (`data/tasas.json`) vía `RepositorioTasaJSON` (`persistence/repositorios.py`). Modelo de **registro único** (no historial en el MVP): `guardar` sobrescribe el único registro; `obtener_actual` lo devuelve o `None` si no hay.
