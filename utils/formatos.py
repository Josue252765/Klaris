"""Formateo de montos monetarios y fechas a texto legible."""

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from core.moneda import Moneda

_SIMBOLOS_MONEDA = {
    Moneda.USD: "$",
    Moneda.BS: "Bs",
}


def formatear_moneda(monto: Decimal, moneda: Moneda) -> str:
    """Formatea un monto Decimal con el símbolo de la moneda y 2 decimales."""
    if not isinstance(monto, Decimal):
        raise TypeError("El monto debe ser Decimal.")
    simbolo = _SIMBOLOS_MONEDA.get(moneda)
    if simbolo is None:
        raise ValueError(f"Moneda no soportada: {moneda}.")
    redondeado = monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{simbolo} {redondeado}"


def formatear_fecha(fecha: date | datetime) -> str:
    """Formatea una fecha o datetime a formato dd/mm/yyyy."""
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    if not isinstance(fecha, date):
        raise TypeError("Se esperaba una fecha o datetime.")
    return fecha.strftime("%d/%m/%Y")


def formatear_fecha_hora(fecha: datetime) -> str:
    """Formatea un datetime a formato dd/mm/yyyy HH:MM."""
    if not isinstance(fecha, datetime):
        raise TypeError("Se esperaba un datetime.")
    return fecha.strftime("%d/%m/%Y %H:%M")
