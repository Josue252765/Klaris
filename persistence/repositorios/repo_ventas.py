"""Repositorio de Venta sobre JSON."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from core.moneda import Moneda
from core.ventas import ItemCarrito, Venta
from persistence.json_store import JsonStore


class RepositorioVentasJSON:
    """Persistencia de Venta en data/ventas.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/ventas.json"))

    def guardar(self, venta: Venta) -> None:
        """Persiste una venta como diccionario."""
        self._store.guardar(self._serializar(venta))

    def listar(self) -> list[Venta]:
        """Devuelve todas las ventas."""
        return [self._deserializar(r) for r in self._store.listar()]

    def actualizar(self, venta: Venta) -> None:
        """Reemplaza la venta con el mismo id."""
        self._store.actualizar(self._serializar(venta))

    def _serializar(self, v: Venta) -> dict:
        return {
            "id": v.id,
            "items": [
                {
                    "producto_id": i.producto_id,
                    "cantidad": i.cantidad,
                    "precio_unitario": str(i.precio_unitario),
                }
                for i in v.items
            ],
            "total": str(v.total),
            "moneda": v.moneda.value,
            "metodo_pago": v.metodo_pago,
            "fecha": v.fecha.isoformat(),
            "total_bs": str(v.total_bs) if v.total_bs is not None else None,
            "tasa_usada": str(v.tasa_usada) if v.tasa_usada is not None else None,
            "monto_recibido_bs": str(v.monto_recibido_bs) if v.monto_recibido_bs is not None else None,
            "vuelto_bs": str(v.vuelto_bs) if v.vuelto_bs is not None else None,
            "anulada": v.anulada,
            "cliente_id": v.cliente_id,
        }

    def _deserializar(self, r: dict) -> Venta:
        items = [
            ItemCarrito(
                producto_id=i["producto_id"],
                cantidad=i["cantidad"],
                precio_unitario=Decimal(i["precio_unitario"]),
            )
            for i in r["items"]
        ]
        return Venta(
            id=r["id"],
            items=items,
            total=Decimal(r["total"]),
            moneda=Moneda(r["moneda"]),
            metodo_pago=r["metodo_pago"],
            fecha=datetime.fromisoformat(r["fecha"]),
            total_bs=Decimal(r["total_bs"]) if r.get("total_bs") is not None else None,
            tasa_usada=Decimal(r["tasa_usada"]) if r.get("tasa_usada") is not None else None,
            monto_recibido_bs=Decimal(r["monto_recibido_bs"]) if r.get("monto_recibido_bs") is not None else None,
            vuelto_bs=Decimal(r["vuelto_bs"]) if r.get("vuelto_bs") is not None else None,
            anulada=bool(r.get("anulada", False)),
            cliente_id=r.get("cliente_id"),
        )
