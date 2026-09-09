"""Control de stock: entradas, salidas, ajustes y alertas de stock bajo."""

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Literal, Protocol

from core.producto import Producto, RepositorioProductos
from utils.excepciones import (
    ProductoNoEncontradoError,
    StockInsuficienteError,
    ValorInvalidoError,
)


@dataclass(frozen=True)
class MovimientoStock:
    """Registro inmutable de un cambio de stock, para trazabilidad."""

    producto_id: str
    tipo: Literal["entrada", "salida", "ajuste"]
    cantidad: int
    motivo: str
    fecha: datetime = field(default_factory=datetime.now)


class RepositorioMovimientos(Protocol):
    """Contrato de persistencia de movimientos de stock."""

    def guardar(self, movimiento: MovimientoStock) -> None: ...


class GestorInventario:
    """Único punto de entrada para modificar el stock de un producto."""

    def __init__(
        self,
        productos: RepositorioProductos,
        movimientos: RepositorioMovimientos,
    ) -> None:
        self._productos = productos
        self._movimientos = movimientos

    def registrar_entrada(
        self, producto_id: str, cantidad: int, motivo: str
    ) -> MovimientoStock:
        """Incrementa el stock y registra el movimiento; lanza si el producto falta."""
        producto = self._buscar_producto(producto_id)
        self._validar_cantidad_positiva(cantidad)
        movimiento = self._crear_movimiento(producto_id, "entrada", cantidad, motivo)
        self._movimientos.guardar(movimiento)
        self._productos.actualizar(replace(producto, stock_actual=producto.stock_actual + cantidad))
        return movimiento

    def registrar_salida(
        self, producto_id: str, cantidad: int, motivo: str
    ) -> MovimientoStock:
        """Decrementa el stock si hay suficiente; lanza StockInsuficienteError si no."""
        producto = self._buscar_producto(producto_id)
        self._validar_cantidad_positiva(cantidad)
        if cantidad > producto.stock_actual:
            raise StockInsuficienteError(
                f"Stock insuficiente: hay {producto.stock_actual}, se pide {cantidad}."
            )
        movimiento = self._crear_movimiento(producto_id, "salida", cantidad, motivo)
        self._movimientos.guardar(movimiento)
        self._productos.actualizar(replace(producto, stock_actual=producto.stock_actual - cantidad))
        return movimiento

    def ajustar_stock(
        self, producto_id: str, nueva_cantidad: int, motivo: str
    ) -> MovimientoStock:
        """Fija el stock a un valor exacto; lanza ValorInvalidoError si es negativo."""
        if nueva_cantidad < 0:
            raise ValorInvalidoError("La nueva cantidad no puede ser negativa.")
        producto = self._buscar_producto(producto_id)
        movimiento = self._crear_movimiento(producto_id, "ajuste", nueva_cantidad, motivo)
        self._movimientos.guardar(movimiento)
        self._productos.actualizar(replace(producto, stock_actual=nueva_cantidad))
        return movimiento

    def productos_stock_bajo(self) -> list[Producto]:
        """Devuelve los productos cuyo stock actual es menor o igual al mínimo."""
        return [
            p for p in self._productos.listar()
            if p.stock_actual <= p.stock_minimo
        ]

    def _buscar_producto(self, producto_id: str) -> Producto:
        producto = self._productos.obtener(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError(f"No existe un producto con id {producto_id}.")
        return producto

    def _validar_cantidad_positiva(self, cantidad: int) -> None:
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
            raise ValorInvalidoError("La cantidad debe ser un entero positivo.")

    def _crear_movimiento(
        self, producto_id: str, tipo: str, cantidad: int, motivo: str
    ) -> MovimientoStock:
        return MovimientoStock(
            producto_id=producto_id,
            tipo=tipo,  # type: ignore[arg-type]
            cantidad=cantidad,
            motivo=motivo,
        )