# Módulo: backup y exportaciones CSV

Responsabilidad: respaldar los JSON operativos y generar archivos tabulares a partir de gestores existentes.

## Backup

`persistence/backup.py` expone `crear_backup(directorio_datos, directorio_backups) -> Path`.
Crea `backup_<timestamp>/`, copia allí todos los `.json` del directorio de datos y devuelve la ruta creada.
El backup v1/MVP se ejecuta bajo demanda, conserva los JSON sin comprimir y no incluye restauración automática.
La compresión, restauración y validación de integridad quedan como mejora v2.

## Exportaciones

`exportacion/csv_reportes.py` escribe en `exports/` por defecto y devuelve la ruta de cada CSV.
No lee JSON directamente: recibe los gestores y usa sus métodos públicos.

| Función | Fuente pública |
|---|---|
| `exportar_catalogo_productos` | `GestorProductos.listar` y `CalculadoraPrecios.precio_venta` |
| `exportar_ventas` | `GestorVentas.listar` |
| `exportar_gastos` | `GestorGastos.listar` |
| `exportar_cierre_caja` | `GeneradorReportes.cierre_de_caja` |
| `exportar_cuentas_por_cobrar` | `GestorClientes.listar_clientes` y `obtener_saldo_deuda` |
| `exportar_movimientos_inventario` | `GestorInventario.historial_movimientos` |

`exportar_gastos` admite rango y categoría opcionales, y conserva `monto_original`, `moneda_original` y `tasa_usada` para trazabilidad.
Los montos se convierten directamente de `Decimal` a `str`. `fecha_corte` en cuentas por cobrar es la fecha de corte del saldo agregado.

## CLI

El menú principal ofrece `9. Backup y exportación`, con una opción para el backup y una para cada CSV. La salida pasa a la opción `10`.
