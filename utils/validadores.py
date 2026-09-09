"""Validadores helper para entradas de texto, montos y opciones."""

from decimal import Decimal


def validar_texto_no_vacio(valor: str, campo: str = "valor") -> str:
    """Valida que un texto no sea None, vacío ni solo espacios; lo devuelve limpio."""
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"El {campo} no puede estar vacío.")
    return valor.strip()


def validar_texto_longitud(
    valor: str, maximo: int, campo: str = "valor"
) -> str:
    """Valida que un texto no exceda la longitud máxima; lo devuelve limpio."""
    texto = validar_texto_no_vacio(valor, campo)
    if len(texto) > maximo:
        raise ValueError(f"El {campo} no puede superar {maximo} caracteres.")
    return texto


def validar_monto_positivo(monto: Decimal, campo: str = "monto") -> Decimal:
    """Valida que un monto sea Decimal y mayor a cero; lo devuelve."""
    if not isinstance(monto, Decimal):
        raise TypeError(f"El {campo} debe ser Decimal.")
    if monto <= 0:
        raise ValueError(f"El {campo} debe ser mayor a cero.")
    return monto


def validar_monto_no_negativo(monto: Decimal, campo: str = "monto") -> Decimal:
    """Valida que un monto sea Decimal y no negativo; lo devuelve."""
    if not isinstance(monto, Decimal):
        raise TypeError(f"El {campo} debe ser Decimal.")
    if monto < 0:
        raise ValueError(f"El {campo} no puede ser negativo.")
    return monto


def validar_opcion(valor: str, opciones: set[str], campo: str = "opción") -> str:
    """Valida que un valor esté dentro de las opciones permitidas; lo devuelve."""
    if valor not in opciones:
        raise ValueError(
            f"{campo.capitalize()} inválida: '{valor}'. "
            f"Opciones: {', '.join(sorted(opciones))}."
        )
    return valor


def validar_entero_positivo(valor: int, campo: str = "cantidad") -> int:
    """Valida que un entero sea positivo (> 0); lo devuelve."""
    if not isinstance(valor, int) or isinstance(valor, bool) or valor <= 0:
        raise ValueError(f"El {campo} debe ser un entero positivo.")
    return valor
