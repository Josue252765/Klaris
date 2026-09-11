"""Repositorios de Cliente y Abono sobre JSON."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from core.clientes import Abono, Cliente
from persistence.json_store import JsonStore


class RepositorioClientesJSON:
    """Persistencia de Cliente en data/clientes.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/clientes.json"))

    def guardar(self, cliente: Cliente) -> None:
        """Persiste un cliente como diccionario."""
        self._store.guardar(self._serializar(cliente))

    def obtener(self, id: str) -> Cliente | None:
        """Busca un cliente por id; devuelve None si no existe."""
        registro = self._store.obtener(id)
        return self._deserializar(registro) if registro else None

    def listar(self) -> list[Cliente]:
        """Devuelve todos los clientes."""
        return [self._deserializar(r) for r in self._store.listar()]

    def _serializar(self, c: Cliente) -> dict:
        return {
            "id": c.id,
            "nombre": c.nombre,
            "cedula_rif": c.cedula_rif,
            "telefono": c.telefono,
        }

    def _deserializar(self, r: dict) -> Cliente:
        return Cliente(
            id=r["id"],
            nombre=r["nombre"],
            cedula_rif=r["cedula_rif"],
            telefono=r["telefono"],
        )


class RepositorioAbonosJSON:
    """Persistencia de Abono en data/abonos.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/abonos.json"))

    def guardar(self, abono: Abono) -> None:
        """Persiste un abono como diccionario."""
        self._store.guardar(self._serializar(abono))

    def listar(self) -> list[Abono]:
        """Devuelve todos los abonos."""
        return [self._deserializar(r) for r in self._store.listar()]

    def _serializar(self, a: Abono) -> dict:
        return {
            "id": a.id,
            "cliente_id": a.cliente_id,
            "monto_usd": str(a.monto_usd),
            "monto_bs": str(a.monto_bs) if a.monto_bs is not None else None,
            "tasa_usada": str(a.tasa_usada) if a.tasa_usada is not None else None,
            "metodo_pago": a.metodo_pago,
            "fecha": a.fecha.isoformat(),
            "nota": a.nota,
        }

    def _deserializar(self, r: dict) -> Abono:
        return Abono(
            id=r["id"],
            cliente_id=r["cliente_id"],
            monto_usd=Decimal(r["monto_usd"]),
            monto_bs=Decimal(r["monto_bs"]) if r.get("monto_bs") is not None else None,
            tasa_usada=Decimal(r["tasa_usada"]) if r.get("tasa_usada") is not None else None,
            metodo_pago=r["metodo_pago"],
            fecha=datetime.fromisoformat(r["fecha"]),
            nota=r.get("nota"),
        )
