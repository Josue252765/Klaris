"""Repositorio de Producto sobre JSON."""

from decimal import Decimal
from pathlib import Path

from core.producto import Producto
from persistence.json_store import JsonStore


class RepositorioProductosJSON:
    """Persistencia de Producto en data/productos.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/productos.json"))

    def guardar(self, producto: Producto) -> None:
        """Persiste un producto como diccionario."""
        self._store.guardar(self._serializar(producto))

    def obtener(self, id: str) -> Producto | None:
        """Busca un producto por id; devuelve None si no existe."""
        registro = self._store.obtener(id)
        return self._deserializar(registro) if registro else None

    def listar(self) -> list[Producto]:
        """Devuelve todos los productos."""
        return [self._deserializar(r) for r in self._store.listar()]

    def actualizar(self, producto: Producto) -> None:
        """Reemplaza el producto con el mismo id."""
        self._store.actualizar(self._serializar(producto))

    def _serializar(self, p: Producto) -> dict:
        return {
            "id": p.id,
            "nombre": p.nombre,
            "categoria": p.categoria,
            "costo_unitario": str(p.costo_unitario),
            "margen_ganancia": str(p.margen_ganancia),
            "stock_actual": p.stock_actual,
            "stock_minimo": p.stock_minimo,
            "unidad_medida": p.unidad_medida,
            "codigo": p.codigo,
            "activo": p.activo,
        }

    def _deserializar(self, r: dict) -> Producto:
        return Producto(
            id=r["id"],
            nombre=r["nombre"],
            categoria=r["categoria"],
            costo_unitario=Decimal(r["costo_unitario"]),
            margen_ganancia=Decimal(r["margen_ganancia"]),
            stock_actual=r["stock_actual"],
            stock_minimo=r["stock_minimo"],
            unidad_medida=r["unidad_medida"],
            codigo=r["codigo"],
            activo=r["activo"],
        )
