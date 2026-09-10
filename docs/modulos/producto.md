# Módulo: core/producto.py

Responsabilidad: CRUD de productos e inventario base.

## Clase `Producto` (`@dataclass`)

| Atributo | Tipo | Regla |
|---|---|---|
| `id` | `str` | UUID4, generado al crear, inmutable |
| `nombre` | `str` | no vacío, máx 100 caracteres |
| `categoria` | `str` | no vacío |
| `costo_unitario` | `Decimal` | en USD, nunca negativo |
| `margen_ganancia` | `Decimal` | porcentaje, ej. `Decimal("30")` = 30% |
| `stock_actual` | `int` | nunca negativo |
| `stock_minimo` | `int` | nunca negativo |
| `unidad_medida` | `str` | "unidad", "kg", "litro", etc. — no vacío, máx 20 caracteres |
| `codigo` | `str` | autogenerado, formato `PREFIJO-NNNN` (ej. `ALI-0001`), único |
| `activo` | `bool` | default `True` |

El `codigo` es autogenerado: prefijo = primeras 3 letras de la categoría en mayúsculas (sin acentos ni espacios) + número secuencial zero-padded a 4 dígitos. El usuario nunca lo escribe ni lo ve como entrada; se usa para búsqueda rápida (y preparación para lector de código de barras).

Todas las validaciones anteriores ocurren en `__init__`/construcción → `ValorInvalidoError` si se violan.

Eliminación: siempre soft delete (`activo = False`). Nunca borrar físicamente — preserva integridad histórica de ventas pasadas.

## Clase `GestorProductos`

| Firma | Retorna | Lanza |
|---|---|---|
| `crear(nombre, categoria, costo_unitario, margen, stock_inicial, stock_minimo, unidad) -> Producto` | producto creado | `ValorInvalidoError` |
| `obtener(id: str) -> Producto` | producto | `ProductoNoEncontradoError` si no existe |
| `obtener_por_codigo(codigo: str) -> Producto` | producto | `ProductoNoEncontradoError` si no existe |
| `actualizar(id: str, **campos) -> Producto` | producto actualizado | `ProductoNoEncontradoError`, `ValorInvalidoError` |
| `desactivar(id: str) -> None` | — | `ProductoNoEncontradoError` |
| `listar(solo_activos: bool = True) -> list[Producto]` | lista | — |
| `buscar_por_nombre(texto: str) -> list[Producto]` | lista | — |
