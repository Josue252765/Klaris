# Estado de Klaris

> El agente debe leer este archivo al empezar cada sesión y actualizarlo al terminar. No lo reescribas completo: agrega/edita solo lo que cambió.

## Fase actual

- **Completadas:** setup, moneda (enum), producto, precios, inventario, ventas, gastos, persistencia (json_store + 4 repositorios), config/settings, utils/formatos, utils/validadores — 106/106 tests pasando.
- **Pendiente del MVP:** moneda (TasaCambio), main.py.
- **Fuera de alcance (v2, no tocar):** empleados, auth, SQLite, reportes, web.

## Últimas sesiones

_(el agente agrega una línea nueva al final de cada sesión, formato: fecha — qué se hizo — estado de tests)_

- 2026-09-09 — Documentación inicial (spec + AGENTS.md) creada. Aún sin trabajo de código en esta sesión de OpenCode.
- 2026-09-09 — Implementados core/producto.py + core/precios.py con tests. 23/23 pasando.
- 2026-09-09 — Implementado core/inventario.py (MovimientoStock + GestorInventario) con tests. 34/34 pasando.
- 2026-09-09 — Implementados core/moneda.py (enum) + core/ventas.py (Carrito, Venta, GestorVentas) con tests. 48/48 pasando.
- 2026-09-09 — Implementado core/gastos.py (CategoriaGasto, Gasto, GestorGastos) con tests. 60/60 pasando. Decisión registrada en DECISIONES.md sobre total_periodo sin TasaCambio.
- 2026-09-09 — Implementada persistencia: json_store.py (escritura atómica) + repositorios.py (4 repositorios JSON con serialización Decimal/datetime/enum). 80/80 pasando.
- 2026-09-09 — Implementados config/settings.py (Settings central), utils/formatos.py (moneda+fechas), utils/validadores.py (texto/montos/opciones) con tests. 106/106 pasando.

## Decisiones pendientes / dudas abiertas

_(cosas que el agente no debe decidir solo — preguntarte a ti)_

- Ninguna todavía.

## Bugs conocidos

_(ninguno aún)_
