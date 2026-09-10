"""Gestión de tasas de cambio: actualizar y consultar la tasa vigente."""

from datetime import date
from decimal import Decimal

from core.moneda import RepositorioTasa, TasaCambio
from utils.excepciones import ValorInvalidoError


class GestorTasas:
    """Administra la tasa de cambio vigente sobre un repositorio inyectado."""

    def __init__(self, repositorio: RepositorioTasa) -> None:
        self._repositorio = repositorio

    def obtener_actual(self) -> TasaCambio | None:
        """Devuelve la tasa vigente o None si no hay ninguna guardada."""
        return self._repositorio.obtener_actual()

    def actualizar(
        self, tasa_referencial: Decimal, tasa_diaria: Decimal
    ) -> TasaCambio:
        """Crea y guarda una nueva tasa con la fecha de hoy; la devuelve."""
        self._validar_tasa(tasa_referencial, "tasa_referencial")
        self._validar_tasa(tasa_diaria, "tasa_diaria")
        tasa = TasaCambio(
            tasa_referencial=tasa_referencial,
            tasa_referencial_fecha=date.today(),
            tasa_diaria=tasa_diaria,
            tasa_diaria_fecha=date.today(),
        )
        self._repositorio.guardar(tasa)
        return tasa

    def _validar_tasa(self, valor: Decimal, campo: str) -> None:
        if not isinstance(valor, Decimal):
            raise ValorInvalidoError(f"{campo} debe ser Decimal, nunca float.")
        if valor <= 0:
            raise ValorInvalidoError(f"{campo} debe ser mayor a cero.")
