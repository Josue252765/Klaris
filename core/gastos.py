"""Registro de egresos operativos: gastos por categoría y total por período."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Protocol
from uuid import uuid4

from core.moneda import Moneda, RepositorioTasa
from utils.excepciones import MonedaInvalidaError, ValorInvalidoError


class CategoriaGasto(Enum):
    """Clasificación de un gasto operativo."""

    MERCANCIA = "MERCANCIA"
    SERVICIOS = "SERVICIOS"
    SUELDOS = "SUELDOS"
    OTROS = "OTROS"


@dataclass(frozen=True)
class Gasto:
    """Egreso operativo registrado: monto en USD, con trazabilidad de origen."""

    id: str
    categoria: CategoriaGasto
    descripcion: str
    monto: Decimal
    moneda: Moneda
    fecha: datetime = field(default_factory=datetime.now)
    monto_original: Decimal | None = None
    moneda_original: Moneda | None = None
    tasa_usada: Decimal | None = None


class RepositorioGastos(Protocol):
    """Contrato de persistencia de gastos."""

    def guardar(self, gasto: Gasto) -> None: ...

    def listar(self) -> list[Gasto]: ...


class GestorGastos:
    """CRUD y agregaciones de gastos sobre repositorios inyectados."""

    def __init__(
        self,
        repositorio: RepositorioGastos,
        repo_tasa: RepositorioTasa | None = None,
    ) -> None:
        self._repositorio = repositorio
        self._repo_tasa = repo_tasa

    def registrar(
        self,
        categoria: CategoriaGasto,
        descripcion: str,
        monto: Decimal,
        moneda: Moneda,
    ) -> Gasto:
        """Crea, valida y persiste un gasto; convierte BS a USD con tasa diaria."""
        self._validar_descripcion(descripcion)
        self._validar_monto(monto)
        self._validar_moneda(moneda)
        monto_usd, monto_orig, moneda_orig, tasa = self._normalizar_monto(monto, moneda)
        gasto = Gasto(
            id=str(uuid4()),
            categoria=categoria,
            descripcion=descripcion,
            monto=monto_usd,
            moneda=Moneda.USD,
            monto_original=monto_orig,
            moneda_original=moneda_orig,
            tasa_usada=tasa,
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
        """Suma los gastos del rango; todos están en USD (convertidos al registrar)."""
        gastos = self.listar(desde=desde, hasta=hasta)
        total = Decimal("0")
        for gasto in gastos:
            total += gasto.monto
        return total

    def _normalizar_monto(
        self, monto: Decimal, moneda: Moneda
    ) -> tuple[Decimal, Decimal, Moneda, Decimal | None]:
        """Devuelve (monto_usd, monto_original, moneda_original, tasa_usada)."""
        if moneda == Moneda.USD:
            return monto, monto, moneda, None
        tasa = self._obtener_tasa_diaria()
        monto_usd = tasa.convertir(monto, Moneda.BS, Moneda.USD, "diaria")
        return monto_usd, monto, moneda, tasa.tasa_diaria

    def _obtener_tasa_diaria(self):
        if self._repo_tasa is None:
            raise MonedaInvalidaError(
                "No hay repositorio de tasa configurado para convertir BS."
            )
        tasa = self._repo_tasa.obtener_actual()
        if tasa is None:
            raise MonedaInvalidaError("No hay tasa diaria guardada para convertir BS.")
        return tasa

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