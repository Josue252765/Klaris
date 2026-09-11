"""Repositorio de Gasto sobre JSON."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from core.gastos import CategoriaGasto, Gasto
from core.moneda import Moneda
from persistence.json_store import JsonStore


class RepositorioGastosJSON:
    """Persistencia de Gasto en data/gastos.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/gastos.json"))

    def guardar(self, gasto: Gasto) -> None:
        """Persiste un gasto como diccionario."""
        self._store.guardar(self._serializar(gasto))

    def listar(self) -> list[Gasto]:
        """Devuelve todos los gastos."""
        return [self._deserializar(r) for r in self._store.listar()]

    def _serializar(self, g: Gasto) -> dict:
        return {
            "id": g.id,
            "categoria": g.categoria.value,
            "descripcion": g.descripcion,
            "monto": str(g.monto),
            "moneda": g.moneda.value,
            "fecha": g.fecha.isoformat(),
            "monto_original": str(g.monto_original) if g.monto_original is not None else None,
            "moneda_original": g.moneda_original.value if g.moneda_original is not None else None,
            "tasa_usada": str(g.tasa_usada) if g.tasa_usada is not None else None,
        }

    def _deserializar(self, r: dict) -> Gasto:
        return Gasto(
            id=r["id"],
            categoria=CategoriaGasto(r["categoria"]),
            descripcion=r["descripcion"],
            monto=Decimal(r["monto"]),
            moneda=Moneda(r["moneda"]),
            fecha=datetime.fromisoformat(r["fecha"]),
            monto_original=Decimal(r["monto_original"]) if r.get("monto_original") is not None else None,
            moneda_original=Moneda(r["moneda_original"]) if r.get("moneda_original") is not None else None,
            tasa_usada=Decimal(r["tasa_usada"]) if r.get("tasa_usada") is not None else None,
        )
