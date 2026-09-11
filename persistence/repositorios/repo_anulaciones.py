"""Repositorio de AnulacionVenta sobre JSON."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from core.devoluciones import AnulacionVenta
from persistence.json_store import JsonStore


class RepositorioAnulacionesJSON:
    """Persistencia de AnulacionVenta en data/anulaciones.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/anulaciones.json"))

    def guardar(self, anulacion: AnulacionVenta) -> None:
        """Persiste una anulación como diccionario."""
        self._store.guardar(self._serializar(anulacion))

    def listar(self) -> list[AnulacionVenta]:
        """Devuelve todas las anulaciones."""
        return [self._deserializar(r) for r in self._store.listar()]

    def _serializar(self, a: AnulacionVenta) -> dict:
        return {
            "id": a.id,
            "venta_id": a.venta_id,
            "motivo": a.motivo,
            "fecha": a.fecha.isoformat(),
            "monto_devuelto_usd": str(a.monto_devuelto_usd),
        }

    def _deserializar(self, r: dict) -> AnulacionVenta:
        return AnulacionVenta(
            id=r["id"],
            venta_id=r["venta_id"],
            motivo=r["motivo"],
            fecha=datetime.fromisoformat(r["fecha"]),
            monto_devuelto_usd=Decimal(r["monto_devuelto_usd"]),
        )
