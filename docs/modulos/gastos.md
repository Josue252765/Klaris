# Módulo: core/gastos.py

Responsabilidad: registro de egresos operativos.

## Enum `CategoriaGasto`

`MERCANCIA`, `SERVICIOS`, `SUELDOS`, `OTROS`

## Clase `Gasto` (`@dataclass`)

| Atributo | Tipo |
|---|---|
| `id` | `str` (UUID4) |
| `categoria` | `CategoriaGasto` |
| `descripcion` | `str` |
| `monto` | `Decimal` |
| `moneda` | `Moneda` |
| `fecha` | `datetime` |

## Clase `GestorGastos`

| Firma | Retorna |
|---|---|
| `registrar(categoria, descripcion, monto, moneda) -> Gasto` | gasto creado |
| `listar(desde: date = None, hasta: date = None, categoria: CategoriaGasto = None) -> list[Gasto]` | lista filtrada |
| `total_periodo(desde: date, hasta: date) -> Decimal` | total normalizado a USD |
