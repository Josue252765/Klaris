# Módulo: core/moneda.py

Responsabilidad: manejo dual Bs/USD. USD es la moneda base interna para todo cálculo/almacenamiento. Bs es vista derivada de la tasa vigente.

## Clases

| Clase | Atributos | Tipo |
|---|---|---|
| `Moneda` (Enum) | `USD`, `BS` | str |
| `TasaCambio` | `valor` | `Decimal` (Bs por 1 USD) |
| | `fecha_actualizacion` | `date` |

## Métodos

| Firma | Retorna | Lanza |
|---|---|---|
| `TasaCambio.convertir(monto: Decimal, origen: Moneda, destino: Moneda) -> Decimal` | monto convertido | `MonedaInvalidaError` si origen/destino no son del enum `Moneda` |

## Reglas

- La tasa se actualiza manualmente por el usuario (config). No hay integración con API externa de tasa en el MVP.
- `valor` siempre representa Bs por 1 USD, nunca al revés.
