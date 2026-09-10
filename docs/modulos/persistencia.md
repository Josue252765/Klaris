# Módulo: persistence/json_store.py y repositorios.py

Responsabilidad: único punto de contacto con disco. `core/` no sabe que existe JSON.

## Clase `JsonStore` (genérica — no conoce productos/ventas/gastos)

| Firma | Retorna |
|---|---|
| `__init__(filepath: Path)` | — |
| `guardar(registro: dict) -> None` | — |
| `obtener(id: str) -> dict \| None` | registro o `None` |
| `listar() -> list[dict]` | registros |
| `actualizar(registro: dict) -> None` | — |

## Repositorios (`RepositorioProductosJSON`, `RepositorioVentasJSON`, `RepositorioGastosJSON`, `RepositorioMovimientosJSON`, `RepositorioTasaJSON`)

Cada uno envuelve un `JsonStore` y hace la conversión objeto ↔ dict. Aísla a `core/` del formato de almacenamiento — esto es lo que permite migrar a SQLite en v2 sin tocar `core/`.

`RepositorioTasaJSON` es especial: gestiona un **registro único** (la tasa vigente), no una lista de entidades. `guardar` sobrescribe el único registro; `obtener_actual` lo devuelve o `None`.

## Archivos de datos (nombres exactos, no inventar otros)

| Repositorio | Archivo |
|---|---|
| `RepositorioProductosJSON` | `data/productos.json` |
| `RepositorioVentasJSON` | `data/ventas.json` |
| `RepositorioGastosJSON` | `data/gastos.json` |
| `RepositorioMovimientosJSON` | `data/movimientos_stock.json` |
| `RepositorioTasaJSON` | `data/tasas.json` (registro único) |

Cada archivo contiene una lista JSON de objetos (`[]` si está vacío). Si el archivo no existe al leer, `JsonStore` lo crea vacío — no lanza error.

## Reglas técnicas obligatorias

- Escritura siempre atómica: escribir a archivo temporal y `rename` (evita corrupción si el proceso se interrumpe a media escritura).
- `Decimal` no es serializable en JSON nativo → convertir a `str` al guardar, reconstruir con `Decimal(str)` al leer. Nunca pasar por `float`.
- `Enum` (Moneda, CategoriaGasto) → serializar por su `.value`, reconstruir con el enum al leer.
- `datetime`/`date` → serializar en formato ISO 8601 (`.isoformat()`), reconstruir con `fromisoformat()`.

## Inyección

Los `Gestor*` de `core/` reciben su repositorio en el constructor, no lo instancian internamente. Ejemplo de forma esperada:

```python
gestor_ventas = GestorVentas(
    venta_repo=RepositorioVentasJSON(...),
    inventario=GestorInventario(movimiento_repo=RepositorioMovimientosJSON(...))
)
```
