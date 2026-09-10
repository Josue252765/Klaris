# Módulo: core/producto.py

Responsabilidad: CRUD de productos e inventario base.

## Clase `Producto` (`@dataclass`, `frozen=True`)

| Atributo | Tipo | Regla |
|---|---|---|
| `id` | `str` | UUID4, generado al crear, inmutable |
| `nombre` | `str` | no vacío, máx 100 caracteres |
| `categoria` | `str` | no vacío |
| `costo_unitario` | `Decimal` | **siempre en USD** (convertido al crear/editar si el usuario lo ingresó en BS); nunca negativo |
| `margen_ganancia` | `Decimal` | porcentaje, ej. `Decimal("30")` = 30% |
| `stock_actual` | `int` | nunca negativo |
| `stock_minimo` | `int` | nunca negativo |
| `unidad_medida` | `str` | no vacío, máx 20 caracteres |
| `codigo` | `str` | autogenerado, formato `PREFIJO-NNNN` (ej. `ALI-0001`), único |
| `activo` | `bool` | default `True` |

El `codigo` es autogenerado: prefijo = primeras 3 letras de la categoría en mayúsculas (sin acentos ni espacios) + número secuencial zero-padded a 4 dígitos. El usuario nunca lo escribe ni lo ve como entrada; se usa para búsqueda rápida.

Todas las validaciones ocurren en `__post_init__` → `ValorInvalidoError` si se violan.

Eliminación: siempre soft delete (`activo = False`). Nunca borrar físicamente — preserva integridad histórica de ventas pasadas.

## Parámetro `costo_moneda` en `GestorProductos`

El parámetro `costo_moneda: Moneda` (default `Moneda.USD`) indica la moneda en que el usuario está expresando `costo_unitario` al llamar a `crear` o `actualizar`. No se almacena en el `Producto`; es solo un indicador de conversión.

- Si `costo_moneda == Moneda.USD`: el valor se guarda tal cual.
- Si `costo_moneda == Moneda.BS`: se convierte a USD usando `tasa_referencial` antes de guardar. Requiere un `RepositorioTasa` con tasa cargada → `MonedaInvalidaError` si falta.

El atributo `costo_unitario` del `Producto` **siempre representa USD**, independientemente de cómo lo ingresó el usuario.

## Clase `GestorProductos`

`GestorProductos` recibe `repositorio: RepositorioProductos` y opcionalmente `repo_tasa: RepositorioTasa | None`.

| Firma | Retorna | Lanza |
|---|---|---|
| `crear(nombre, categoria, costo_unitario, margen_ganancia, stock_inicial, stock_minimo, unidad_medida, costo_moneda=Moneda.USD) -> Producto` | producto creado | `ValorInvalidoError`, `MonedaInvalidaError` |
| `obtener(id: str) -> Producto` | producto | `ProductoNoEncontradoError` si no existe |
| `obtener_por_codigo(codigo: str) -> Producto` | producto | `ProductoNoEncontradoError` si no existe |
| `actualizar(id: str, costo_moneda=Moneda.USD, **campos) -> Producto` | producto actualizado | `ProductoNoEncontradoError`, `ValorInvalidoError`, `MonedaInvalidaError` |
| `desactivar(id: str) -> None` | — | `ProductoNoEncontradoError` |
| `listar(solo_activos: bool = True) -> list[Producto]` | lista | — |
| `buscar_por_nombre(texto: str) -> list[Producto]` | lista | — |

En `actualizar`, si `"costo_unitario"` está en `campos` y `costo_moneda == Moneda.BS`, el valor se convierte a USD antes de reconstruir el producto. El `id` no se puede modificar; incluirlo en `campos` lanza `ValorInvalidoError`.

## Flujo CLI — edición de costo

En `accion_editar_producto`: si el usuario ingresa un nuevo costo, se pregunta inmediatamente la moneda de ese costo (`pedir_moneda`). Si no ingresa costo, `costo_moneda` queda en `Moneda.USD` y no se incluye en `campos`.

## Persistencia (`data/productos.json`)

```json
{
  "id": "str (UUID4)",
  "nombre": "str",
  "categoria": "str",
  "costo_unitario": "str Decimal (USD)",
  "margen_ganancia": "str Decimal",
  "stock_actual": 0,
  "stock_minimo": 0,
  "unidad_medida": "str",
  "codigo": "ALI-0001",
  "activo": true
}
```

`costo_moneda` no se persiste — solo existe como argumento de entrada al crear/editar.
