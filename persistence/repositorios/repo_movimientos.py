"""Repositorio de MovimientoStock sobre JSON."""

from datetime import datetime
from pathlib import Path

from core.inventario import MovimientoStock
from persistence.json_store import JsonStore


class RepositorioMovimientosJSON:
    """Persistencia de MovimientoStock en data/movimientos_stock.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/movimientos_stock.json"))

    def guardar(self, movimiento: MovimientoStock) -> None:
        """Persiste un movimiento como diccionario."""
        self._store.guardar(self._serializar(movimiento))

    def listar(self) -> list[MovimientoStock]:
        """Devuelve todos los movimientos en orden de registro."""
        return [self._deserializar(r) for r in self._store.listar()]

    def _serializar(self, m: MovimientoStock) -> dict:
        return {
            "producto_id": m.producto_id,
            "tipo": m.tipo,
            "cantidad": m.cantidad,
            "motivo": m.motivo,
            "fecha": m.fecha.isoformat(),
        }

    def _deserializar(self, r: dict) -> MovimientoStock:
        return MovimientoStock(
            producto_id=r["producto_id"],
            tipo=r["tipo"],
            cantidad=r["cantidad"],
            motivo=r["motivo"],
            fecha=datetime.fromisoformat(r["fecha"]),
        )
