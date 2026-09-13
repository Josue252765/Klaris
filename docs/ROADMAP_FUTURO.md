# Roadmap a futuro - Klaris

> Este documento es visión a futuro. No se construye hasta terminar el MVP actual (moneda, producto, precios, inventario, ventas, gastos, persistencia). El orden de construcción sigue siendo el de `docs/ESTADO.md`.

Cada módulo se ubicaría dentro de la estructura actual del repo (`core/`, `persistence/`, `config/`, `utils/`). No se crea `data/`, `services/` ni `ui/` como carpetas separadas - la lógica vive en `core/`, la persistencia en `persistence/`.

## Módulos previstos

### Devoluciones (post-ventas)
- **Archivo:** `core/devoluciones.py`
- **Responsabilidad:** registrar devoluciones de ventas cerradas, reingresar stock vía `GestorInventario.registrar_entrada`, anular o ajustar el total de la venta original.
- **Dependencias:** `core/ventas.py`, `core/inventario.py`, `persistence/repositorios.py`.

### Caja y Turnos
- **Archivo:** `core/caja.py`, `core/turnos.py`
- **Responsabilidad:** apertura/cierre de caja, arqueo (recuento físico vs. sistema), control de turnos de operador. Cada turno consolida ventas y gastos del período.
- **Dependencias:** `core/ventas.py`, `core/gastos.py`, `persistence/repositorios.py`.

### Empleados y Asistencia
- **Archivo:** `core/empleados.py`
- **Responsabilidad:** registro de empleados, control de asistencia (entrada/salida), cálculo de horas. Base para nómina futura (nómina misma fuera de alcance).
- **Dependencias:** `persistence/repositorios.py`, `utils/excepciones.py`.

### Usuarios, Roles y Sesiones
- **Archivo:** `core/usuarios.py`, `core/roles.py`
- **Responsabilidad:** multi-usuario con permisos por rol (admin, cajero, supervisor), inicio/cierre de sesión, control de acceso a operaciones sensibles.
- **Dependencias:** `persistence/repositorios.py`, `utils/excepciones.py`.

### Auditoría
- **Archivo:** `core/auditoria.py`
- **Responsabilidad:** log inmutable de eventos críticos (creación/edición de productos, cierre de ventas, ajustes de stock, cambios de tasa). Solo lectura histórica, nunca editable.
- **Dependencias:** `persistence/json_store.py`, todos los módulos de `core/` que emiten eventos.

### Reportes
- **Archivo:** `core/reportes.py`
- **Responsabilidad:** consolidación de datos existentes en solo lectura: ventas por período, gastos por categoría, margen real, stock valorizado. No genera PDF/Excel en el MVP ampliado.
- **Dependencias:** `core/ventas.py`, `core/gastos.py`, `core/inventario.py`, `core/precios.py`.

### Alertas
- **Archivo:** `core/alertas.py`
- **Responsabilidad:** notificar al dueño de condiciones: stock bajo (ya existe `productos_stock_bajo` en inventario), tasa diaria sin actualizar hace >24h, margen negativo en un producto, venta con monto inusual.
- **Dependencias:** `core/inventario.py`, `core/moneda.py`, `core/precios.py`, `core/ventas.py`.

### Backup avanzado y Restauración (v2)
- **Archivo:** `persistence/backup.py`
- **Base v1/MVP:** backup bajo demanda de los JSON crudos en una carpeta con marca de tiempo, sin compresión ni restauración automática.
- **Mejora v2:** comprimir los backups, restaurarlos y validar su integridad al restaurar.
- **Dependencias:** `persistence/json_store.py`, `config/settings.py`.

### Licencias (protección del software)
- **Archivo:** `core/licencias.py`
- **Responsabilidad:** validación de licencia de uso (clave única por instalación), bloqueo de operación si la licencia expira o es inválida. No implementa DRM complejo - solo verificación básica offline.
- **Dependencias:** `persistence/repositorios.py`, `utils/excepciones.py`.
