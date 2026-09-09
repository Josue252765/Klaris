# Módulo: persistence/json_store.py y repositorios.py

Responsabilidad: único punto de contacto con disco. `core/` no sabe que existe JSON.

## Clase `JsonStore` (genérica — no conoce productos/ventas/gastos)

| Firma | Retorna |
|---|---|
| `__init__(filepath: Path)` | — |
| `leer_todos() -> list[dict]` | registros |
| `guardar_todos(registros: list[dict]) -> None` | — |
| `agregar(registro: dict) -> None` | — |
| `actualizar(id: str, cambios: dict) -> None` | — |
| `eliminar(id: str) -> None` | — |

## Repositorios (`ProductoRepository`, `VentaRepository`, `GastoRepository`, `MovimientoStockRepository`)

Cada uno envuelve un `JsonStore` y hace la conversión objeto ↔ dict. Aísla a `core/` del formato de almacenamiento — esto es lo que permite migrar a SQLite en v2 sin tocar `core/`.

## Reglas técnicas obligatorias

- Escritura siempre atómica: escribir a archivo temporal y `rename` (evita corrupción si el proceso se interrumpe a media escritura).
- `Decimal` no es serializable en JSON nativo → convertir a `str` al guardar, reconstruir con `Decimal(str)` al leer. Nunca pasar por `float`.
- `Enum` (Moneda, CategoriaGasto) → serializar por su `.value`, reconstruir con el enum al leer.
- `datetime`/`date` → serializar en formato ISO 8601 (`.isoformat()`), reconstruir con `fromisoformat()`.

## Inyección

Los `Gestor*` de `core/` reciben su repositorio en el constructor, no lo instancian internamente. Ejemplo de forma esperada:

```python
gestor_ventas = GestorVentas(
    venta_repo=VentaRepository(...),
    inventario=GestorInventario(movimiento_repo=...)
)
```
