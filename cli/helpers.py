"""Funciones helper de la CLI: conversión de input y utilidades de impresión."""

import re
from decimal import Decimal

from core.moneda import Moneda
from core.producto import GestorProductos
from core.ventas import Carrito, METODOS_PAGO_VALIDOS
from utils.excepciones import KlarisError, ProductoNoEncontradoError, ValorInvalidoError
from utils.formatos import formatear_fecha_hora, formatear_moneda


def pedir_moneda(prompt: str) -> Moneda:
    """Pide USD o BS por teclado, tolerando texto extra; lanza ValorInvalidoError si no hay."""
    texto = input(f"{prompt} (USD/BS): ").lower()
    if re.search(r"\busd\b", texto):
        return Moneda.USD
    if re.search(r"\bbs\b", texto):
        return Moneda.BS
    raise ValorInvalidoError("Moneda inválida. Use USD o BS.")


def pedir_decimal(prompt: str) -> Decimal:
    """Pide un Decimal por teclado; lanza ValueError si no es numérico."""
    return Decimal(input(f"{prompt}: "))


def pedir_int(prompt: str) -> int:
    """Pide un entero por teclado; lanza ValueError si no es entero."""
    return int(input(f"{prompt}: "))


def armar_carrito(gestor_productos: GestorProductos) -> Carrito:
    """Construye un carrito pidiendo productos hasta que el usuario diga 'listo'."""
    carrito = Carrito()
    while True:
        entrada = input("Producto (nombre/código) o 'listo': ").strip()
        if entrada.lower() == "listo":
            break
        try:
            producto = _buscar_producto(gestor_productos, entrada)
            if producto is None:
                continue
            cantidad = int(input("Cantidad: "))
            carrito.agregar_item(producto, cantidad)
            print(f"  +{cantidad} {producto.nombre} (total: {carrito.total()})")
        except (KlarisError, ValueError) as e:
            print(f"  Error: {e}")
    return carrito


def seleccionar_producto(gestor: GestorProductos):
    """Pide un texto y resuelve un producto por código o nombre."""
    texto = input("Producto (nombre/código): ").strip()
    return _buscar_producto(gestor, texto)


def _buscar_producto(gestor: GestorProductos, texto: str):
    """Resuelve un producto por código exacto o búsqueda por nombre."""
    try:
        return gestor.obtener_por_codigo(texto)
    except ProductoNoEncontradoError:
        pass
    resultados = gestor.buscar_por_nombre(texto)
    if not resultados:
        print("Producto no encontrado.")
        return None
    if len(resultados) == 1:
        return resultados[0]
    for i, p in enumerate(resultados, start=1):
        print(f"  {i}. [{p.codigo}] {p.nombre} (stock {p.stock_actual})")
    numero = input("Seleccione número: ").strip()
    try:
        indice = int(numero)
    except ValueError:
        return None
    if 1 <= indice <= len(resultados):
        return resultados[indice - 1]
    return None


def pedir_metodo_pago() -> str:
    """Pide el método de pago y lo valida contra los permitidos."""
    metodo = input(
        "Método de pago (efectivo_usd/efectivo_bs/pago_movil/otro/credito): "
    ).strip()
    if metodo not in METODOS_PAGO_VALIDOS:
        raise ValorInvalidoError(f"Método de pago inválido: {metodo}.")
    return metodo


def pedir_monto_recibido(moneda: Moneda) -> Decimal | None:
    """Pide el monto recibido si la moneda es BS; None si es USD."""
    if moneda != Moneda.BS:
        return None
    return Decimal(input("Monto recibido (BS): "))


def imprimir_ticket(venta, gestor_productos: GestorProductos) -> None:
    """Imprime el ticket de la venta en texto plano."""
    print("\n--- TICKET ---")
    for item in venta.items:
        producto = gestor_productos.obtener(item.producto_id)
        nombre = producto.nombre if producto else "Desconocido"
        linea = item.precio_unitario * item.cantidad
        print(f"  {nombre} x{item.cantidad}  {formatear_moneda(linea, Moneda.USD)}")
    print(f"  TOTAL: {formatear_moneda(venta.total, Moneda.USD)}")
    if venta.total_bs is not None:
        print(f"  Total BS: {formatear_moneda(venta.total_bs, Moneda.BS)}")
    if venta.vuelto_bs is not None:
        print(f"  Recibido: {formatear_moneda(venta.monto_recibido_bs, Moneda.BS)}")
        print(f"  Vuelto: {formatear_moneda(venta.vuelto_bs, Moneda.BS)}")
    print(f"  Pago: {venta.metodo_pago}")
    print(f"  Fecha: {formatear_fecha_hora(venta.fecha)}")
    print("-------------")
