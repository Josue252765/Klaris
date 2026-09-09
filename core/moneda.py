"""Enumerado de monedas del sistema dual Bs/USD."""

from enum import Enum


class Moneda(Enum):
    """Moneda del sistema. USD es base interna; BS es vista derivada de la tasa."""

    USD = "USD"
    BS = "BS"
