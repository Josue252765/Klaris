# Módulo: core/gastos.py

Responsabilidad: registro de egresos operativos con normalización bimonetaria a USD.

## Enum `CategoriaGasto`

| Valor | `value` |
|---|---|
| `MERCANCIA` | `"MERCANCIA"` |
| `SERVICIOS` | `"SERVICIOS"` |
| `SUELDOS` | `"SUELDOS"` |
| `OTROS` | `"OTROS"` |

## Clase `Gasto` (`@dataclass`, `frozen=True`)

| Atributo | Tipo | Requerido | Nota |
|---|---|---|---|
| `id` | `str` (UUID4) | sí | generado al registrar |
| `categoria` | `CategoriaGasto` | sí | — |
| `descripcion` | `str` | sí | no vacío |
| `monto` | `Decimal` | sí | **siempre en USD** (convertido al registrar si el usuario ingresó BS) |
| `moneda` | `Moneda` | sí | siempre `Moneda.USD` en el registro guardado |
| `fecha` | `datetime` | sí | `datetime.now()` al registrar |
| `monto_original` | `Decimal \| None` | no | monto tal como lo ingresó el usuario; `None` si ya era USD |
| `moneda_original` | `Moneda \| None` | no | moneda del ingreso original; `None` si ya era USD |
| `tasa_usada` | `Decimal \| None` | no | valor de `tasa_diaria` usado para la conversión; `None` si ya era USD |

`monto_original`, `moneda_original` y `tasa_usada` sirven para trazabilidad: permiten auditar qué se cobró en BS y qué tasa se aplicó.

## Clase `GestorGastos`

Recibe `repositorio: RepositorioGastos` y opcionalmente `repo_tasa: RepositorioTasa | None`.

### `registrar(categoria, descripcion, monto, moneda) -> Gasto`

- Valida que `descripcion` no esté vacía → `ValorInvalidoError`.
- Valida que `monto > 0` y sea `Decimal` → `ValorInvalidoError`.
- Valida que `moneda` sea instancia de `Moneda` → `MonedaInvalidaError`.
- Si `moneda == Moneda.BS`: convierte `monto` a USD usando `tasa_diaria` del `RepositorioTasa`. Requiere tasa cargada → `MonedaInvalidaError` si falta.
- Persiste el gasto con `monto` en USD y los campos `monto_original`/`moneda_original`/`tasa_usada` poblados.

### `listar(desde=None, hasta=None, categoria=None) -> list[Gasto]`

Filtra por rango de fechas (ambos extremos inclusivos) y/o categoría. Sin argumentos devuelve todos.

### `total_periodo(desde: date, hasta: date) -> Decimal`

Suma `gasto.monto` (USD) de todos los gastos del rango. Como todos los gastos se almacenan en USD, no requiere conversión al calcular el total.

## Impacto bimonetario

El gasto siempre se almacena en USD, garantizando que `total_periodo` sea directamente comparable con el total de ventas (también en USD). La conversión BS→USD se aplica en el momento del registro usando la `tasa_diaria` vigente, no al consultar.

## Flujo CLI (`cli/acciones.py → accion_registrar_gasto`)

1. Mostrar menú: `1=MERCANCIA 2=SERVICIOS 3=SUELDOS 4=OTROS`.
2. Pedir descripción.
3. Pedir monto (`pedir_decimal`).
4. Pedir moneda (`pedir_moneda`): `USD` o `BS`.
5. Llamar a `registrar`; confirmar con `id` y `monto USD` resultante.

## Persistencia (`data/gastos.json`)

```json
{
  "id": "str (UUID4)",
  "categoria": "MERCANCIA | SERVICIOS | SUELDOS | OTROS",
  "descripcion": "str",
  "monto": "str Decimal (USD)",
  "moneda": "USD",
  "fecha": "ISO 8601",
  "monto_original": "str Decimal | null",
  "moneda_original": "USD | BS | null",
  "tasa_usada": "str Decimal | null"
}
```

Todos los `Decimal` se serializan como `str`; se reconstruyen con `Decimal(str)` al leer — nunca pasan por `float`.
