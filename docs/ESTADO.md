# Estado de Klaris

> El agente debe leer este archivo al empezar cada sesión y actualizarlo al terminar. No lo reescribas completo: agrega/edita solo lo que cambió.

## Fase actual

- **Completadas:** MVP Fases 0-6 completo (setup, moneda, producto con código autogenerado, precios, inventario, ventas, gastos, persistencia, config, utils, tasas y CLI).
- **Completadas:** Fase 7 — Reportes y cierre de caja (core/reportes.py, docs/modulos/reportes.md).
- **Completadas:** Fase 8 — Devoluciones y anulaciones (core/devoluciones.py, persistencia, CLI, exclusión en reportes).
- **Pendiente del MVP:** Ninguno.
- **Pendientes no críticos (deuda técnica / documentación):**
  - Tests complementarios en `core/`, `utils/` y `config/`.
  - (resuelto) Sincronización de specs en `docs/modulos/` completada.
  - (resuelto) Spec `docs/modulos/reportes.md` para la Fase 7.
- **Fuera de alcance (v2, no tocar):** empleados, auth, SQLite, reportes Excel/PDF, web.

## Últimas sesiones

_(el agente agrega una línea nueva al final de cada sesión, formato: fecha - qué se hizo - estado de tests)_

- 2026-09-09 - Documentación inicial (spec + AGENTS.md) creada. Aún sin trabajo de código en esta sesión de OpenCode.
- 2026-09-09 - Implementados core/producto.py + core/precios.py con tests. 23/23 pasando.
- 2026-09-09 - Implementado core/inventario.py (MovimientoStock + GestorInventario) con tests. 34/34 pasando.
- 2026-09-09 - Implementados core/moneda.py (enum) + core/ventas.py (Carrito, Venta, GestorVentas) con tests. 48/48 pasando.
- 2026-09-09 - Implementado core/gastos.py (CategoriaGasto, Gasto, GestorGastos) con tests. 60/60 pasando. Decisión registrada en DECISIONES.md sobre total_periodo sin TasaCambio.
- 2026-09-09 - Implementada persistencia: json_store.py (escritura atómica) + repositorios.py (4 repositorios JSON con serialización Decimal/datetime/enum). 80/80 pasando.
- 2026-09-09 - Implementados config/settings.py (Settings central), utils/formatos.py (moneda+fechas), utils/validadores.py (texto/montos/opciones) con tests. 106/106 pasando.
- 2026-09-09 - Implementado TasaCambio en core/moneda.py + RepositorioTasaJSON en persistence/repositorios.py + ruta_tasas() en config/settings.py con tests. 117/117 pasando. Decisión registrada en DECISIONES.md (archivo propio sobre ampliar Settings).
- 2026-09-10 - Corrección de bugs críticos de MVP (menú inventario, edición de costo de producto, validación de pago en BS) resueltos en commit afa21ba. 161/161 tests pasando.
- 2026-09-10 - Sincronización de specs docs/modulos/ (5 archivos actualizados). Sin cambios de código.
- 2026-09-10 - Fase 7: core/reportes.py (GeneradorReportes, CierreCaja, ProductoRanking), tests/core/test_reportes.py (16 tests), integración CLI y main.py. 177/177 tests pasando.
- 2026-09-10 - Spec docs/modulos/reportes.md. Fase 8: AnulacionVenta, GestorDevoluciones.anular_venta, persistencia, CLI y exclusión en reportes. 187/187 tests pasando.

## Decisiones pendientes / dudas abiertas

_(cosas que el agente no debe decidir solo - preguntarte a ti)_

- Ninguna todavía.

## Bugs conocidos

_(ninguno aún)_

## Roadmap a futuro

Ver `docs/ROADMAP_FUTURO.md` - módulos previstos post-MVP. No se construyen hasta terminar el MVP actual.
