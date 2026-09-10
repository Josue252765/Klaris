# Klaris

Sistema de gestión financiera y control de inventario para bodegas y pequeños comercios en Venezuela.
Desarrollado en Python puro, 100% offline, con persistencia en JSON y soporte para doble denominación monetaria (USD y BS).

## Características principales

- **Productos:** Catálogo con código autogenerado (`PREFIJO-NNNN`), márgenes de ganancia y costos en USD/BS.
- **Inventario:** Entradas, salidas, ajustes de stock y alertas de stock bajo.
- **Ventas:** Carrito de compras, cobro multimoneda (USD o efectivo/pago móvil en BS) con cálculo automático de vuelto y tasa diaria.
- **Gastos:** Registro categorizado y cálculo de totales normalizados a USD.
- **Tasas:** Control de tasa referencial y tasa diaria.
- **Reportes:** Resumen financiero del día por terminal.

## Ejecución

Requiere Python 3.10 o superior.

```bash
# Iniciar la interfaz de consola interactiva
python3 main.py
```

## Pruebas

El proyecto cuenta con una suite completa de pruebas unitarias y de integración:

```bash
# Ejecutar toda la suite
pytest

# Ejecutar solo tests de lógica de negocio (core)
pytest tests/core/
```

## Estructura del proyecto

```
.
├── main.py              # Punto de entrada y loop del menú interactivo
├── config/              # Configuración general y resolución de rutas de datos
├── core/                # Lógica de negocio pura (moneda, producto, inventario, ventas, gastos, tasas)
├── cli/                 # Acciones de terminal y helpers de interacción
├── persistence/         # Repositorios JSON y almacenamiento atómico
├── utils/               # Validadores, formateadores de moneda/fecha y excepciones de dominio
├── tests/               # Pruebas unitarias, de persistencia, CLI e integración
├── data/                # Archivos JSON locales de persistencia
└── docs/                # Especificaciones de arquitectura, convenciones y módulos
```
