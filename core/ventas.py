"""Carrito temporal, cierre de venta y descuento de stock asociado."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import uuid4

from core.inventario import GestorInventario
from core.moneda import Moneda, RepositorioTasa, TasaCambio
from core.precios import CalculadoraPrecios
from core.producto import Producto, RepositorioProductos
from utils.excepciones import (
    CarritoVacioError,
    MonedaInvalidaError,
    ProductoNoEncontradoError,
    StockInsuficienteError,
    ValorInvalidoError,
)

METODOS_PAGO_VALIDOS = {"efectivo_usd", "efectivo_bs", "pago_movil", "otro"}


@dataclass(frozen=True)
class ItemCarrito:
    """Línea del carrito: snapshot de precio al momento de agregar."""

    producto_id: str
    cantidad: int
    precio_unitario: Decimal


class Carrito:
    """Acumulador temporal de items antes del cierre de venta."""

    def __init__(self) -> None:
        self._items: dict[str, ItemCarrito] = {}

    def agregar_item(self, producto: Producto, cantidad: int) -> None:
        """Agrega un producto validando stock; snapshot del precio al momento."""
        self._validar_cantidad(cantidad)
        self._validar_stock_disponible(producto, cantidad)
        precio = CalculadoraPrecios.precio_venta(
            producto.costo_unitario, producto.margen_ganancia
        )
        actual = self._items.get(producto.id)
        nueva_cantidad = cantidad if actual is None else actual.cantidad + cantidad
        self._items[producto.id] = ItemCarrito(
            producto_id=producto.id, cantidad=nueva_cantidad, precio_unitario=precio
        )

    def quitar_item(self, producto_id: str) -> None:
        """Elimina un item del carrito por id de producto."""
        self._items.pop(producto_id, None)

    def total(self) -> Decimal:
        """Suma del costo total de todos los items del carrito."""
        return sum(
            (item.precio_unitario * item.cantidad for item in self._items.values()),
            Decimal("0"),
        )

    def vaciar(self) -> None:
        """Elimina todos los items del carrito."""
        self._items.clear()

    def esta_vacio(self) -> bool:
        """Devuelve True si el carrito no tiene items."""
        return len(self._items) == 0

    def items(self) -> list[ItemCarrito]:
        """Devuelve una copia de los items del carrito."""
        return list(self._items.values())

    def _validar_cantidad(self, cantidad: int) -> None:
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
            raise ValorInvalidoError("La cantidad debe ser un entero positivo.")

    def _validar_stock_disponible(self, producto: Producto, cantidad: int) -> None:
        acumulado = self._items.get(producto.id)
        total_pedido = cantidad if acumulado is None else acumulado.cantidad + cantidad
        if total_pedido > producto.stock_actual:
            raise StockInsuficienteError(
                f"Stock insuficiente: hay {producto.stock_actual}, se pide {total_pedido}."
            )


@dataclass(frozen=True)
class Venta:
    """Venta cerrada: snapshot inmutable de items, total y datos de pago."""

    id: str
    items: list[ItemCarrito]
    total: Decimal
    moneda: Moneda
    metodo_pago: str
    fecha: datetime = field(default_factory=datetime.now)
    total_bs: Decimal | None = None
    tasa_usada: Decimal | None = None
    monto_recibido_bs: Decimal | None = None
    vuelto_bs: Decimal | None = None


class RepositorioVentas(Protocol):
    """Contrato de persistencia de ventas."""

    def guardar(self, venta: Venta) -> None: ...


class GestorVentas:
    """Cierra ventas validando stock atómicamente antes de descontar nada."""

    def __init__(
        self,
        inventario: GestorInventario,
        productos: RepositorioProductos,
        ventas: RepositorioVentas,
        repo_tasa: RepositorioTasa | None = None,
    ) -> None:
        self._inventario = inventario
        self._productos = productos
        self._ventas = ventas
        self._repo_tasa = repo_tasa

    def cerrar_venta(
        self,
        carrito: Carrito,
        moneda: Moneda,
        metodo_pago: str,
        moneda_pago: Moneda = Moneda.USD,
        monto_recibido_bs: Decimal | None = None,
    ) -> Venta:
        """Valida, descuenta stock, persiste y devuelve la venta cerrada."""
        self._validar_carrito_no_vacio(carrito)
        self._validar_metodo_pago(metodo_pago)
        self._validar_stock_de_todo(carrito)
        self._descontar_stock(carrito)
        venta = self._construir_venta(
            carrito, moneda, metodo_pago, moneda_pago, monto_recibido_bs
        )
        self._ventas.guardar(venta)
        return venta

    def _validar_carrito_no_vacio(self, carrito: Carrito) -> None:
        if carrito.esta_vacio():
            raise CarritoVacioError("No se puede cerrar una venta con el carrito vacío.")

    def _validar_metodo_pago(self, metodo_pago: str) -> None:
        if metodo_pago not in METODOS_PAGO_VALIDOS:
            raise ValorInvalidoError(f"Método de pago inválido: {metodo_pago}.")

    def _validar_stock_de_todo(self, carrito: Carrito) -> None:
        for item in carrito.items():
            producto = self._productos.obtener(item.producto_id)
            if producto is None:
                raise ProductoNoEncontradoError(
                    f"No existe un producto con id {item.producto_id}."
                )
            if item.cantidad > producto.stock_actual:
                raise StockInsuficienteError(
                    f"Stock insuficiente para {producto.nombre}: "
                    f"hay {producto.stock_actual}, se pide {item.cantidad}."
                )

    def _descontar_stock(self, carrito: Carrito) -> None:
        for item in carrito.items():
            self._inventario.registrar_salida(
                item.producto_id, item.cantidad, "venta"
            )

    def _construir_venta(
        self,
        carrito: Carrito,
        moneda: Moneda,
        metodo_pago: str,
        moneda_pago: Moneda,
        monto_recibido_bs: Decimal | None,
    ) -> Venta:
        total_usd = carrito.total()
        if moneda_pago == Moneda.BS:
            total_bs, tasa, vuelto = self._calcular_pago_bs(total_usd, monto_recibido_bs)
        else:
            total_bs, tasa, vuelto = None, None, None
        return Venta(
            id=str(uuid4()),
            items=carrito.items(),
            total=total_usd,
            moneda=moneda,
            metodo_pago=metodo_pago,
            total_bs=total_bs,
            tasa_usada=tasa,
            monto_recibido_bs=monto_recibido_bs,
            vuelto_bs=vuelto,
        )

    def _calcular_pago_bs(
        self, total_usd: Decimal, monto_recibido_bs: Decimal | None
    ) -> tuple[Decimal, Decimal, Decimal | None]:
        tasa = self._obtener_tasa_diaria()
        total_bs = tasa.convertir(total_usd, Moneda.USD, Moneda.BS, "diaria")
        vuelto = self._calcular_vuelto(monto_recibido_bs, total_bs)
        return total_bs, tasa.tasa_diaria, vuelto

    def _obtener_tasa_diaria(self) -> TasaCambio:
        if self._repo_tasa is None:
            raise MonedaInvalidaError(
                "No hay repositorio de tasa configurado para pago en BS."
            )
        tasa = self._repo_tasa.obtener_actual()
        if tasa is None:
            raise MonedaInvalidaError("No hay tasa diaria guardada para pago en BS.")
        return tasa

    def _calcular_vuelto(
        self, monto_recibido: Decimal | None, total: Decimal
    ) -> Decimal | None:
        if monto_recibido is None:
            return None
        if monto_recibido < total:
            raise ValorInvalidoError(
                f"Pago insuficiente: {monto_recibido} < {total}."
            )
        return monto_recibido - total