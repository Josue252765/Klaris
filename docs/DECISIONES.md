# Decisiones de diseño — Klaris

> Cada vez que se tome una decisión que se desvía de `docs/modulos/*.md` o `docs/01_ARQUITECTURA.md`, o que la spec deja ambigua, se registra aquí con fecha y razón. El agente debe revisar este archivo antes de tomar decisiones de arquitectura — si algo ya se decidió aquí, no lo cambia sin preguntar primero.

## Formato de cada entrada

```
### [fecha] Título corto de la decisión
- Contexto: por qué surgió la duda
- Decisión: qué se decidió
- Razón: por qué
```

## Registro

### [2026-09-09] total_periodo de gastos: normalización a USD con TasaCambio integrado
- Contexto: `gastos.md` define `total_periodo` como "total normalizado a USD". Originalmente `TasaCambio` no existía y `total_periodo` lanzaba `MonedaInvalidaError` para gastos en BS. Hoy `TasaCambio` está implementado e integrado en `GestorGastos`: los gastos en BS se convierten a USD con `tasa_diaria` al momento del registro, y `total_periodo` simplemente suma el campo `monto` (ya en USD).
- Decisión: `total_periodo` suma directamente el campo `monto` de cada gasto (todos en USD tras la conversión al registrar). No recalcular con la tasa actual — así nunca cambia retroactivamente.
- Razón: la promesa "el dueño nunca pierde un centavo" exige que un gasto registrado no cambie de valor si la tasa de hoy cambia. Fijar el monto en USD al registrar lo resuelve.

### [2026-09-09] margen_real lanza ValorInvalidoError si costo == 0
- Contexto: `precios.md` dejaba la columna "Lanza" de `margen_real` vacía. El código ya lanzaba `ValorInvalidoError` cuando `costo == 0` (división por cero), pero no estaba documentado en la spec.
- Decisión: mantener el guard en el código y documentar en `precios.md` que `margen_real` lanza `ValorInvalidoError` si `costo == 0`.
- Razón: calcular un margen con costo cero no tiene sentido matemático ni de negocio. Lanzar una excepción clara es más honesto que devolver un valor arbitrario.

### [2026-09-09] unidad_medida: validador propio con límite de 20 caracteres
- Contexto: `producto.py` validaba `unidad_medida` con `_validar_nombre`, imponiendo el límite de 100 caracteres del nombre. La spec `producto.md` no definía regla de validación para `unidad_medida`.
- Decisión: crear `_validar_unidad_medida` con límite de 20 caracteres (no 100) y documentar la regla en `producto.md`.
- Razón: las unidades de medida reales ("unidad", "kg", "litro") son cortas; 100 caracteres es excesivo y reutilizar `_validar_nombre` era un atajo que imponía una restricción sin sustento.

### [2026-09-09] JsonStore: renombrar métodos para coincidir con Protocols de core/
- Contexto: `JsonStore` usaba nombres (`leer_todos`, `guardar_todos`, `agregar`, `actualizar(id, cambios)`, `eliminar`) distintos a los de los Protocols de `core/` (`guardar`, `obtener`, `listar`, `actualizar`). La brecha de nombrado no estaba documentada.
- Decisión: renombrar los métodos de `JsonStore` a `guardar`, `obtener`, `listar`, `actualizar(registro)` para coincidir con los Protocols. Eliminar `guardar_todos` y `eliminar` (no usados). Actualizar `persistencia.md`.
- Razón: alinear los nombres reduce fricción cognitiva y elimina la necesidad de traducción mental entre la spec y el código. Los métodos eliminados no eran consumidos por ningún repositorio.

### [2026-09-09] utils/validadores.py y config/settings.py: ValorInvalidoError en vez de ValueError nativo
- Contexto: `validadores.py` y `settings.py` lanzaban `ValueError` nativo de Python, mientras que el resto de `core/` usa `ValorInvalidoError` (que hereda de `KlarisError`). Esto rompía la jerarquía de excepciones de dominio definida en `02_CONVENCIONES.md`.
- Decisión: reemplazar todo `ValueError` por `ValorInvalidoError` de `utils/excepciones.py`. Mantener `TypeError` donde era apropiado (tipo incorrecto, no valor inválido). Ajustar tests.
- Razón: mantener una sola jerarquía de excepciones de dominio permite que `main.py` capture `KlarisError` al nivel superior sin漏ar excepciones nativas.

### [2026-09-09] TasaCambio: persistencia en archivo propio (no ampliar Settings)
- Contexto: había dos opciones para persistir `TasaCambio`: (A) ampliar `config/settings.py` con los atributos de tasa, o (B) crear `data/tasas.json` con `RepositorioTasaJSON` en `persistence/repositorios.py`.
- Decisión: opción B — archivo propio `data/tasas.json` con `RepositorioTasaJSON`, modelo de registro único.
- Razón: las tasas son datos operacionales que cambian a diario, no configuración estática como el nombre del negocio. Separarlas evita que `Settings` crezca en responsabilidad más allá de su rol y mantiene el patrón de "cada entidad con su repositorio". Si mañana se quiere historial de tasas, el repositorio ya existe y solo se amplía.

### [2026-09-09] Código de producto autogenerado (PREFIJO-NNNN)
- Contexto: hacía falta una forma corta y única de identificar/buscar productos sin depender del UUID ni del nombre libre (que admite mayúsculas, errores de tipeo y duplicados).
- Decisión: `Producto.codigo` se autogenera en `GestorProductos.crear()` a partir de las primeras 3 letras de la categoría (mayúsculas, sin acentos ni espacios) + número secuencial zero-padded a 4 dígitos. El usuario nunca lo escribe.
- Razón: evitar error humano al tipearlo y garantizar unicidad, y dejar preparado el terreno para un lector de código de barras futuro (PATRÓN corto y estable).

### [2026-09-10] anular_venta vive en GestorDevoluciones
- Contexto: la tarea permitía el método en `core/ventas.py` o `core/devoluciones.py`.
- Decisión: `GestorDevoluciones.anular_venta` orquesta validación, reingreso de stock y persistencia de `AnulacionVenta`. `GestorVentas` solo expone `obtener` y `marcar_anulada`.
- Razón: anular no es cerrar una venta; mezclarlo en `GestorVentas` acoplaría ventas a un repositorio de anulaciones. El flag `anulada` sí pertenece a `Venta` porque los reportes y el listado lo leen ahí.
