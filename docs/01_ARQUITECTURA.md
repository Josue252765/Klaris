# Arquitectura — Klaris backend

## Reglas inquebrantables

- `core/` = lógica de negocio pura. Cero I/O. Cero imports de `persistence/` en la lógica interna de una clase; los repositorios se inyectan por constructor.
- `persistence/` gestiona JSON y backups; `exportacion/` escribe únicamente CSV. Nada fuera de esos límites toca disco.
- Ningún módulo de `core/` modifica datos de otro módulo directamente — siempre a través de su interfaz pública (métodos), nunca accediendo a atributos internos de otra clase.
- Ninguna función/método > 30 líneas. Si se excede, dividir.
- Ningún archivo > 300 líneas. Si se excede, dividir en submódulos.
- Todo método/función pública: docstring de una línea (qué hace, qué recibe, qué devuelve, qué excepción lanza). Nada de relleno.
- Dinero: siempre `Decimal`, nunca `float`. Conversión a `str` al serializar a JSON, reconstrucción con `Decimal(str)` al leer — nunca pasar por `float` en el camino.
- IDs de entidad: `str(uuid4())`.
- POO desde el inicio: cada entidad de negocio es una clase (`@dataclass` donde aplique), no un diccionario suelto.
- Inyección de dependencias: los `Gestor*`/`Calculadora*` reciben su repositorio en el constructor. Tests de `core/` no tocan disco — usan repos falsos in-memory.

## Estructura de carpetas

```
klaris/
├── main.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── core/
│   ├── __init__.py
│   ├── moneda.py
│   ├── producto.py
│   ├── precios.py
│   ├── inventario.py
│   ├── ventas.py
│   ├── gastos.py
│   ├── reportes.py
│   └── devoluciones.py
├── persistence/
│   ├── __init__.py
│   ├── json_store.py
│   └── repositorios.py
├── exportacion/
│   └── csv_reportes.py
├── utils/
│   ├── __init__.py
│   ├── validadores.py
│   ├── formatos.py
│   └── excepciones.py
├── data/
├── tests/
│   ├── core/
│   └── persistence/
├── docs/
├── requirements.txt
├── README.md
└── .gitignore
```

## Fuera de alcance (MVP) — no implementar, no dejar ganchos

Empleados/nómina · auth/roles · SQLite · reportes Excel/PDF · web/API HTTP · multi-tenant.
