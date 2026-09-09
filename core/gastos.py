"""Registro de egresos operativos: gastos por categoría y total por período."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Protocol
from uuid import uuid4

from core.moneda import Moneda
from utils.excepciones import MonedaInvalidaError, ValorInvalidoError


class CategoriaGasto(Enum):
    """Clasificación de un gasto operativo."""

    MERCANCIA = "MERCANCIA"
    SERVICIOS = "SERVICIOS"
    SUELDOS = "SUELDOS"
    OTROS = "OTROS"


@dataclass(frozen=True)
class Gasto:
    """Egreso operativo registrado: monto, categoría, moneda y fecha."""

    id: str
    categoria: CategoriaGasto
    descripcion: str
    monto: Decimal
    moneda: Moneda
    fecha: datetime = field(default_factory=datetime.now)


class RepositorioGastos(Protocol):
    """Contrato de persistencia de gastos."""

    def guardar(self, gasto: Gasto) -> None: ...

    def listar(self) -> list[Gasto]: ...


class GestorGastos:
    """CRUD y agregaciones de gastos sobre un repositorio inyectado."""

    def __init__(self, repositorio: RepositorioGastos) -> None:
        self._repositorio = repositorio

    def registrar(
        self,
        categoria: CategoriaGasto,
        descripcion: str,
        monto: Decimal,
        moneda: Moneda,
    ) -> Gasto:
        """Crea, valida y persiste un gasto; lanza ValorInvalidoError si monto <= 0."""
        self._validar_descripcion(descripcion)
        self._validar_monto(monto)
        self._validar_moneda(moneda)
        gasto = Gasto(
            id=str(uuid4()),
            categoria=categoria,
            descripcion=descripcion,
            monto=monto,
            moneda=moneda,
        )
        self._repositorio.guardar(gasto)
        return gasto

    def listar(
        self,
        desde: date | None = None,
        hasta: date | None = None,
        categoria: CategoriaGasto | None = None,
    ) -> list[Gasto]:
        """Lista gastos filtrando por rango de fechas y categoría."""
        gastos = self._repositorio.listar()
        return [
            g for g in gastos
            if self._pasa_filtro_fecha(g, desde, hasta)
            and (categoria is None or g.categoria == categoria)
        ]

    def total_periodo(self, desde: date, hasta: date) -> Decimal:
        """Suma los gastos del rango normalizados a USD; lanza si hay BS sin tasa."""
        gastos = self.listar(desde=desde, hasta=hasta)
        total = Decimal("0")
        for gasto in gastos:
            total += self._normalizar_a_usd(gasto)
        return total

    def _normalizar_a_usd(self, gasto: Gasto) -> Decimal:
        if gasto.moneda == Moneda.USD:
            return gasto.monto
        raise MonedaInvalidaError(
            "No se puede normalizar a USD: TasaCambio aún no está implementada."
        )

    def _pasa_filtro_fecha(
        self, gasto: Gasto, desde: date | None, hasta: date | None
    ) -> bool:
        fecha_gasto = gasto.fecha.date()
        if desde is not None and fecha_gasto < desde:
            return False
        if hasta is not None and fecha_gasto > hasta:
            return False
        return True

    def _validar_descripcion(self, descripcion: str) -> None:
        if not isinstance(descripcion, str) or not descripcion.strip():
            raise ValorInvalidoError("La descripción no puede estar vacía.")

    def _validar_monto(self, monto: Decimal) -> None:
        if not isinstance(monto, Decimal):
            raise ValorInvalidoError("El monto debe ser Decimal, nunca float.")
        if monto <= 0:
            raise ValorInvalidoError("El monto debe ser mayor a cero.")

    def _validar_moneda(self, moneda: Moneda) -> None:
        if not isinstance(moneda, Moneda):
            raise MonedaInvalidaError("La moneda debe ser del enum Moneda.")