# AGENTS.md — Klaris

Leído automáticamente antes de cada tarea. No lo borres ni lo dejes desactualizado.

## Orden de lectura obligatorio

1. `docs/00_CONTEXTO.md` — leer UNA sola vez al iniciar el proyecto (no releer en cada tarea).
2. `docs/01_ARQUITECTURA.md` — leer siempre, en toda tarea.
3. `docs/02_CONVENCIONES.md` — leer siempre, en toda tarea.
4. `docs/modulos/<modulo>.md` — leer SOLO el/los módulo(s) relevantes a la tarea actual. No cargar todos los `.md` de `modulos/` de una vez.
5. `docs/ESTADO.md` — leer siempre, para saber en qué fase va el proyecto.
6. `docs/DECISIONES.md` — leer siempre, para no revertir decisiones ya tomadas.

Si una tarea contradice algo en `01_ARQUITECTURA.md`, `02_CONVENCIONES.md` o el `.md` del módulo correspondiente: avisar antes de proceder, no reinterpretar por cuenta propia.

## Reglas no negociables (resumen — el detalle está en `02_CONVENCIONES.md`)

- Cero rastros de generación por IA en código o commits.
- Sin funcionalidad fuera del alcance del MVP (`01_ARQUITECTURA.md` → "Fuera de alcance").
- `Decimal` para todo dinero, nunca `float`.
- Un módulo, sus tests, en el mismo paso — no avanzar con tests rotos.

## Comandos útiles

```
pytest                      # correr toda la suite
pytest tests/core/          # solo lógica de negocio
ruff check .                # lint (si está instalado)
ruff format .                # formateo (si está instalado)
```
