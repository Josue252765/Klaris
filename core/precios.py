"""Motor de cálculo costo → precio de venta. Todo en Decimal, sin pasar por float."""

from decimal import ROUND_HALF_UP, Decimal

from utils.excepciones import ValorInvalidoError


class CalculadoraPrecios:
    """Operaciones de precio basadas en costo y margen, redondeadas a 2 decimales."""

    @staticmethod
    def precio_venta(costo: Decimal, margen_pct: Decimal) -> Decimal:
        """Calcula el precio aplicando el margen; usa ROUND_HALF_UP a 2 decimales."""
        return _aplicar_margen(costo, margen_pct)

    @staticmethod
    def precio_mayorista(costo: Decimal, margen_pct: Decimal) -> Decimal:
        """Calcula el precio mayorista con su margen propio; misma fórmula que venta."""
        return _aplicar_margen(costo, margen_pct)

    @staticmethod
    def margen_real(costo: Decimal, precio_venta: Decimal) -> Decimal:
        """Devuelve el porcentaje real de margen dado un precio; lanza si costo es 0."""
        if costo == 0:
            raise ValorInvalidoError("No se puede calcular el margen con costo cero.")
        return ((precio_venta - costo) / costo * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )


def _aplicar_margen(costo: Decimal, margen_pct: Decimal) -> Decimal:
    """Aplica la fórmula costo * (1 + margen/100) con redondeo monetario."""
    return (costo * (Decimal("1") + margen_pct / Decimal("100"))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )