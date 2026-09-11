"""Acciones de CLI relacionadas con Tasas de Cambio."""

from core.tasas import GestorTasas
from cli.helpers import pedir_decimal
from utils.excepciones import KlarisError


def accion_actualizar_tasa(gestor: GestorTasas) -> None:
    """Actualiza la tasa de cambio pidiendo referencial y diaria."""
    try:
        ref = pedir_decimal("Tasa referencial (Bs por USD)")
        diaria = pedir_decimal("Tasa diaria (Bs por USD)")
        tasa = gestor.actualizar(ref, diaria)
        print(f"OK: tasa actualizada (ref={tasa.tasa_referencial}, "
              f"diaria={tasa.tasa_diaria})")
    except (KlarisError, ValueError, ArithmeticError) as e:
        print(f"Error: {e}")


def accion_ver_tasa(gestor: GestorTasas) -> None:
    """Muestra la tasa de cambio vigente o avisa si no hay."""
    tasa = gestor.obtener_actual()
    if tasa is None:
        print("No hay tasa guardada.")
        return
    print(f"Tasa referencial: {tasa.tasa_referencial} (fecha: {tasa.tasa_referencial_fecha})")
    print(f"Tasa diaria: {tasa.tasa_diaria} (fecha: {tasa.tasa_diaria_fecha})")
