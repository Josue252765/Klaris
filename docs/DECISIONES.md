# Decisiones de diseño — Klaris

> Cada vez que se tome una decisión que se desvía de `KLARIS_BACKEND_SPEC.md`, o que la spec deja ambigua, se registra aquí con fecha y razón. El agente debe revisar este archivo antes de tomar decisiones de arquitectura — si algo ya se decidió aquí, no lo cambia sin preguntar primero.

## Formato de cada entrada

```
### [fecha] Título corto de la decisión
- Contexto: por qué surgió la duda
- Decisión: qué se decidió
- Razón: por qué
```

## Registro

### [2026-09-09] total_periodo de gastos: normalización a USD sin TasaCambio
- Contexto: `gastos.md` define `total_periodo` como "total normalizado a USD", pero `TasaCambio` (módulo `core/moneda.py`) aún no está implementado — solo existe el enum `Moneda`.
- Decisión: `total_periodo` suma directamente los gastos en USD; si encuentra un gasto en BS lanza `MonedaInvalidaError` indicando que TasaCambio no está implementada.
- Razón: no inventar una conversión sin tasa real violaría la promesa "el dueño nunca pierde un centavo". Mejor fallar honestamente que suponer una tasa ficticia.

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
