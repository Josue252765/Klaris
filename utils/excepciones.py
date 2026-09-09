"""Jerarquía de excepciones de dominio. Todas derivan de KlarisError."""


class KlarisError(Exception):
    """Excepción base del dominio de Klaris."""


class ValorInvalidoError(KlarisError):
    """Un valor de entrada no cumple las reglas del dominio."""


class ProductoNoEncontradoError(KlarisError):
    """No existe un producto con el identificador solicitado."""


class StockInsuficienteError(KlarisError):
    """La operación requiere más stock del disponible."""


class CarritoVacioError(KlarisError):
    """No se puede cerrar una venta con el carrito vacío."""


class MonedaInvalidaError(KlarisError):
    """La moneda indicada no pertenece al enum Moneda."""


class PersistenciaError(KlarisError):
    """Error al leer o escribir el almacenamiento en disco."""