"""Anulación de ventas cerradas y reingreso de stock asociado."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import uuid4

from core.inventario import GestorInventario
from core.ventas import GestorVentas, Venta
from utils.excepciones import ValorInvalidoError


@dataclass(frozen=True)
class AnulacionVenta:
    """Registro inmutable de una anulación de venta."""

    id: str
    venta_id: str
    motivo: str
    fecha: datetime
    monto_devuelto_usd: Decimal


class RepositorioAnulaciones(Protocol):
    """Contrato de persistencia de anulaciones."""

    def guardar(self, anulacion: AnulacionVenta) -> None: ...

    def listar(self) -> list[AnulacionVenta]: ...


class GestorDevoluciones:
    """Anula ventas, reingresa stock y persiste la anulación."""

    def __init__(
        self,
        gestor_ventas: GestorVentas,
        inventario: GestorInventario,
        anulaciones: RepositorioAnulaciones,
    ) -> None:
        self._ventas = gestor_ventas
        self._inventario = inventario
        self._anulaciones = anulaciones

    def anular_venta(self, venta_id: str, motivo: str) -> AnulacionVenta:
        """Anula una venta, reingresa stock y persiste; lanza si no existe o ya está anulada."""
        self._validar_motivo(motivo)
        venta = self._obtener_venta_anulable(venta_id)
        self._reingresar_stock(venta)
        self._ventas.marcar_anulada(venta.id)
        anulacion = self._construir_anulacion(venta, motivo)
        self._anulaciones.guardar(anulacion)
        return anulacion

    def _validar_motivo(self, motivo: str) -> None:
        if not isinstance(motivo, str) or not motivo.strip():
            raise ValorInvalidoError("El motivo de anulación no puede estar vacío.")

    def _obtener_venta_anulable(self, venta_id: str) -> Venta:
        venta = self._ventas.obtener(venta_id)
        if venta is None:
            raise ValorInvalidoError(f"No existe una venta con id {venta_id}.")
        if venta.anulada:
            raise ValorInvalidoError("La venta ya está anulada.")
        return venta

    def _reingresar_stock(self, venta: Venta) -> None:
        for item in venta.items:
            self._inventario.registrar_entrada(
                item.producto_id, item.cantidad, f"anulación venta {venta.id}"
            )

    def _construir_anulacion(self, venta: Venta, motivo: str) -> AnulacionVenta:
        return AnulacionVenta(
            id=str(uuid4()),
            venta_id=venta.id,
            motivo=motivo.strip(),
            fecha=datetime.now(),
            monto_devuelto_usd=venta.total,
        )
