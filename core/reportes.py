"""Generación de reportes de negocio: cierre de caja y ranking de productos."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Protocol

from core.gastos import GestorGastos
from core.moneda import Moneda, RepositorioTasa
from core.ventas import GestorVentas, Venta


@dataclass(frozen=True)
class DesglosePago:
    """Total acumulado para un método de pago específico."""

    metodo: str
    total_usd: Decimal
    cantidad_ventas: int


@dataclass(frozen=True)
class CierreCaja:
    """Resumen financiero de un período: ventas, gastos y balance neto."""

    fecha_desde: date
    fecha_hasta: date
    total_ventas_usd: Decimal
    total_ventas_bs: Decimal
    desglose_pago: list[DesglosePago]
    total_gastos_usd: Decimal
    total_gastos_bs: Decimal
    balance_neto_usd: Decimal


@dataclass(frozen=True)
class ProductoRanking:
    """Posición de un producto en el ranking de ventas."""

    producto_id: str
    cantidad_total: int
    monto_total_usd: Decimal


class RepositorioProductosNombres(Protocol):
    """Subconjunto del contrato de productos que necesita el generador."""

    def obtener(self, id: str): ...


class GeneradorReportes:
    """Compone reportes a partir de gestores de ventas y gastos."""

    _METODOS = ("efectivo_usd", "efectivo_bs", "pago_movil", "otro")

    def __init__(
        self,
        gestor_ventas: GestorVentas,
        gestor_gastos: GestorGastos,
        repo_tasa: RepositorioTasa | None = None,
    ) -> None:
        self._ventas = gestor_ventas
        self._gastos = gestor_gastos
        self._repo_tasa = repo_tasa

    def cierre_de_caja(
        self, fecha_desde: date, fecha_hasta: date | None = None
    ) -> CierreCaja:
        """Genera el cierre del período; si fecha_hasta es None usa fecha_desde."""
        hasta = fecha_hasta if fecha_hasta is not None else fecha_desde
        ventas = self._ventas.listar(desde=fecha_desde, hasta=hasta)
        tasa_diaria = self._tasa_diaria()

        total_ventas_usd = self._sumar_ventas_usd(ventas)
        total_ventas_bs = self._convertir_usd_a_bs(total_ventas_usd, tasa_diaria)
        desglose = self._desglose_por_metodo(ventas)
        total_gastos_usd = self._gastos.total_periodo(fecha_desde, hasta)
        total_gastos_bs = self._convertir_usd_a_bs(total_gastos_usd, tasa_diaria)
        balance = total_ventas_usd - total_gastos_usd

        return CierreCaja(
            fecha_desde=fecha_desde,
            fecha_hasta=hasta,
            total_ventas_usd=total_ventas_usd,
            total_ventas_bs=total_ventas_bs,
            desglose_pago=desglose,
            total_gastos_usd=total_gastos_usd,
            total_gastos_bs=total_gastos_bs,
            balance_neto_usd=balance,
        )

    def top_productos_vendidos(
        self,
        limite: int = 5,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> list[ProductoRanking]:
        """Devuelve los productos más vendidos en cantidad, limitado a 'limite'."""
        ventas = self._ventas.listar(desde=desde, hasta=hasta)
        acumulado: dict[str, list] = {}
        for venta in ventas:
            for item in venta.items:
                pid = item.producto_id
                if pid not in acumulado:
                    acumulado[pid] = [0, Decimal("0")]
                acumulado[pid][0] += item.cantidad
                acumulado[pid][1] += item.precio_unitario * item.cantidad
        ranking = [
            ProductoRanking(
                producto_id=pid,
                cantidad_total=datos[0],
                monto_total_usd=datos[1],
            )
            for pid, datos in acumulado.items()
        ]
        ranking.sort(key=lambda r: r.cantidad_total, reverse=True)
        return ranking[:limite]

    def _sumar_ventas_usd(self, ventas: list[Venta]) -> Decimal:
        return sum((v.total for v in ventas), Decimal("0"))

    def _desglose_por_metodo(self, ventas: list[Venta]) -> list[DesglosePago]:
        totales: dict[str, list] = {m: [Decimal("0"), 0] for m in self._METODOS}
        for venta in ventas:
            if venta.metodo_pago in totales:
                totales[venta.metodo_pago][0] += venta.total
                totales[venta.metodo_pago][1] += 1
        return [
            DesglosePago(
                metodo=metodo,
                total_usd=datos[0],
                cantidad_ventas=datos[1],
            )
            for metodo, datos in totales.items()
        ]

    def _tasa_diaria(self) -> Decimal | None:
        if self._repo_tasa is None:
            return None
        tasa = self._repo_tasa.obtener_actual()
        return tasa.tasa_diaria if tasa is not None else None

    def _convertir_usd_a_bs(
        self, monto_usd: Decimal, tasa: Decimal | None
    ) -> Decimal:
        if tasa is None:
            return Decimal("0")
        from decimal import ROUND_HALF_UP
        return (monto_usd * tasa).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
