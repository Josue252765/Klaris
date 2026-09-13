"""Acciones de CLI relacionadas con Ventas y Devoluciones."""

from decimal import Decimal

from core.clientes import GestorClientes
from core.devoluciones import GestorDevoluciones
from core.moneda import Moneda
from core.producto import GestorProductos
from core.ventas import GestorVentas, Venta
from cli.helpers import (
    armar_carrito,
    imprimir_ticket,
    pedir_metodo_pago,
    pedir_moneda,
    pedir_monto_recibido,
)
from core.configuracion import GestorConfiguracion
from utils.excepciones import KlarisError, ValorInvalidoError
from utils.formatos import formatear_fecha, formatear_moneda


def accion_vender(
    gestor_ventas: GestorVentas,
    gestor_productos: GestorProductos,
    gestor_clientes: GestorClientes | None = None,
    *,
    configuracion: GestorConfiguracion,
) -> None:
    """Arma un carrito, pregunta pago, cierra la venta e imprime el ticket."""
    try:
        carrito = armar_carrito(gestor_productos)
        if carrito.esta_vacio():
            print("Nada que vender.")
            return
        metodo = pedir_metodo_pago()
        cliente_id, moneda_pago, monto_recibido = _datos_cierre_venta(
            metodo, gestor_clientes
        )
        venta = gestor_ventas.cerrar_venta(
            carrito, Moneda.USD, metodo,
            moneda_pago=moneda_pago, monto_recibido_bs=monto_recibido,
            cliente_id=cliente_id,
        )
        conf = configuracion.obtener()
        imprimir_ticket(venta, gestor_productos, conf)
    except (KlarisError, ValueError, ArithmeticError) as e:
        print(f"Error: {e}")


def accion_anular_venta(
    gestor_devoluciones: GestorDevoluciones, gestor_ventas: GestorVentas
) -> None:
    """Lista ventas activas, pide id y motivo, y anula la venta."""
    try:
        ventas = [v for v in gestor_ventas.listar() if not v.anulada]
        if not ventas:
            print("No hay ventas para anular.")
            return
        print("Ventas:")
        for v in ventas:
            print(
                f"  [{v.id[:8]}] {formatear_moneda(v.total, Moneda.USD)} | "
                f"{formatear_fecha(v.fecha)}"
            )
        texto = input("ID de venta: ").strip()
        venta = _resolver_venta_por_id(ventas, texto)
        motivo = input("Motivo: ").strip()
        anulacion = gestor_devoluciones.anular_venta(venta.id, motivo)
        print(f"OK: venta anulada (id={anulacion.venta_id[:8]})")
    except (KlarisError, ValueError) as e:
        print(f"Error: {e}")


def _resolver_venta_por_id(ventas: list[Venta], texto: str) -> Venta:
    if not texto:
        raise ValorInvalidoError("El id de venta no puede estar vacío.")
    coincidencias = [v for v in ventas if v.id.startswith(texto)]
    if len(coincidencias) == 1:
        return coincidencias[0]
    if len(coincidencias) > 1:
        raise ValorInvalidoError(
            "Hay varias ventas con ese prefijo; usa más caracteres del id."
        )
    raise ValorInvalidoError(f"No existe una venta con id {texto}.")


def _datos_cierre_venta(
    metodo: str, gestor_clientes: GestorClientes | None
) -> tuple[str | None, Moneda, Decimal | None]:
    if metodo == "credito":
        if gestor_clientes is None:
            raise ValorInvalidoError("No hay gestor de clientes configurado.")
        cliente = _seleccionar_cliente(gestor_clientes)
        return cliente.id, Moneda.USD, None
    moneda_pago = pedir_moneda("Moneda de pago")
    return None, moneda_pago, pedir_monto_recibido(moneda_pago)


def _seleccionar_cliente(gestor: GestorClientes):
    clientes = gestor.listar_clientes()
    if not clientes:
        raise ValorInvalidoError("No hay clientes registrados.")
    print("Clientes:")
    for c in clientes:
        print(f"  [{c.id[:8]}] {c.nombre} | {c.cedula_rif}")
    texto = input("Cliente (id o cédula): ").strip()
    return _resolver_cliente(clientes, texto)


def _resolver_cliente(clientes, texto: str):
    if not texto:
        raise ValorInvalidoError("El cliente no puede estar vacío.")
    por_cedula = [c for c in clientes if c.cedula_rif.casefold() == texto.casefold()]
    if len(por_cedula) == 1:
        return por_cedula[0]
    por_id = [c for c in clientes if c.id.startswith(texto)]
    if len(por_id) == 1:
        return por_id[0]
    if len(por_id) > 1:
        raise ValorInvalidoError("Hay varios clientes con ese prefijo de id.")
    raise ValorInvalidoError(f"No existe un cliente con '{texto}'.")
