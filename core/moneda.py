"""Enumerado de monedas y gestión de tasas de cambio dual Bs/USD."""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Literal

from utils.excepciones import MonedaInvalidaError, ValorInvalidoError


class Moneda(Enum):
    """Moneda del sistema. USD es base interna; BS es vista derivada de la tasa."""

    USD = "USD"
    BS = "BS"


@dataclass(frozen=True)
class TasaCambio:
    """Tasas de cambio vigentes: referencial (fijar precios) y diaria (cobro/vuelto)."""

    tasa_referencial: Decimal
    tasa_referencial_fecha: date
    tasa_diaria: Decimal
    tasa_diaria_fecha: date

    def __post_init__(self) -> None:
        """Valida que ambas tasas sean Decimal positivos; lanza ValorInvalidoError."""
        self._validar_tasa(self.tasa_referencial, "tasa_referencial")
        self._validar_tasa(self.tasa_diaria, "tasa_diaria")

    def convertir(
        self,
        monto: Decimal,
        origen: Moneda,
        destino: Moneda,
        usar: Literal["referencial", "diaria"],
    ) -> Decimal:
        """Convierte un monto entre monedas usando la tasa indicada; lanza si es inválido."""
        if origen == destino:
            raise MonedaInvalidaError("Origen y destino no pueden ser la misma moneda.")
        tasa = self._obtener_tasa(usar)
        if tasa is None:
            raise MonedaInvalidaError(f"La tasa '{usar}' no está cargada.")
        return self._aplicar_conversion(monto, origen, destino, tasa)

    def _obtener_tasa(self, usar: Literal["referencial", "diaria"]) -> Decimal | None:
        if usar == "referencial":
            return self.tasa_referencial
        if usar == "diaria":
            return self.tasa_diaria
        return None

    def _aplicar_conversion(
        self, monto: Decimal, origen: Moneda, destino: Moneda, tasa: Decimal
    ) -> Decimal:
        if origen == Moneda.USD and destino == Moneda.BS:
            resultado = monto * tasa
        else:
            resultado = monto / tasa
        return resultado.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _validar_tasa(self, valor: Decimal, campo: str) -> None:
        if not isinstance(valor, Decimal):
            raise ValorInvalidoError(f"{campo} debe ser Decimal, nunca float.")
        if valor <= 0:
            raise ValorInvalidoError(f"{campo} debe ser mayor a cero.")
