# Módulo: core/devoluciones.py

Responsabilidad: anular ventas cerradas, reingresar stock y dejar traza de la anulación.

## Clase `AnulacionVenta` (`@dataclass`, `frozen=True`)

| Atributo | Tipo | Nota |
|---|---|---|
| `id` | `str` (UUID4) | generado al anular |
| `venta_id` | `str` | id de la `Venta` original |
| `motivo` | `str` | no vacío |
| `fecha` | `datetime` | `datetime.now()` al anular |
| `monto_devuelto_usd` | `Decimal` | copia de `Venta.total` (siempre USD) |

## Clase `GestorDevoluciones`

Recibe `gestor_ventas: GestorVentas`, `inventario: GestorInventario` y `anulaciones: RepositorioAnulaciones`.

### `anular_venta(venta_id: str, motivo: str) -> AnulacionVenta`

1. Motivo vacío o solo espacios → `ValorInvalidoError`.
2. La venta debe existir → `ValorInvalidoError`.
3. Si `venta.anulada` → `ValorInvalidoError` (no se reingresa stock otra vez).
4. Por cada item: `GestorInventario.registrar_entrada(producto_id, cantidad, motivo de anulación)`.
5. `GestorVentas.marcar_anulada(venta_id)`.
6. Persistir `AnulacionVenta` y devolverla.

No borra la venta: queda en `ventas.json` con `anulada=true`. El cierre de caja y el top de productos ignoran esas ventas (ver `reportes.md`).

## Flujo CLI (`cli/acciones.py → accion_anular_venta`)

1. Listar ventas con `anulada=False` (id corto, total USD, fecha).
2. Pedir id (acepta prefijo único de 8 caracteres).
3. Pedir motivo.
4. Llamar a `anular_venta`; confirmar.

## Persistencia (`data/anulaciones.json`)

```json
{
  "id": "str (UUID4)",
  "venta_id": "str (UUID4)",
  "motivo": "str",
  "fecha": "ISO 8601",
  "monto_devuelto_usd": "str Decimal"
}
```

`RepositorioAnulacionesJSON` en `persistence/repositorios.py`. El flag `anulada` vive en `data/ventas.json`, no en este archivo.
