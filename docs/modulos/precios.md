# Módulo: core/precios.py

Responsabilidad: motor de cálculo costo → precio de venta. Implementa la promesa central: el dueño nunca calcula "a ojo".

## Clase `CalculadoraPrecios`

| Firma | Retorna | Regla |
|---|---|---|
| `precio_venta(costo: Decimal, margen_pct: Decimal) -> Decimal` | precio de venta | fórmula: `costo * (1 + margen_pct / 100)`, redondeo `ROUND_HALF_UP` a 2 decimales |
| `precio_mayorista(costo: Decimal, margen_mayorista_pct: Decimal) -> Decimal` | precio mayorista | misma fórmula, margen distinto |
| `margen_real(costo: Decimal, precio_venta: Decimal) -> Decimal` | % real dado un precio manual | `ValorInvalidoError` si `costo == 0` |

## Reglas

- Margen negativo (precio resultante menor al costo) está PERMITIDO, no se bloquea — pero debe generar una advertencia visible (principio "honestidad en los números"). No lanzar excepción por esto.
- Todo cálculo intermedio en `Decimal`, sin pasar por `float`.
