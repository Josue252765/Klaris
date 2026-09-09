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
