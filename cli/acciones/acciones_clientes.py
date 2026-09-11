"""Acciones de CLI relacionadas con Clientes y Abonos."""

from core.clientes import GestorClientes, METODOS_ABONO_VALIDOS
from core.moneda import Moneda
from cli.helpers import pedir_decimal, pedir_moneda
from utils.excepciones import KlarisError, ValorInvalidoError
from utils.formatos import formatear_moneda


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


def accion_registrar_cliente(gestor: GestorClientes) -> None:
    """Pide datos y registra un cliente nuevo."""
    try:
        nombre = input("Nombre: ").strip()
        cedula = input("Cédula o RIF: ").strip()
        telefono = input("Teléfono: ").strip()
        cliente = gestor.crear_cliente(nombre, cedula, telefono)
        print(f"OK: cliente registrado (id={cliente.id[:8]})")
    except KlarisError as e:
        print(f"Error: {e}")


def accion_ver_clientes_deudas(gestor: GestorClientes) -> None:
    """Lista clientes con su saldo deudor en USD."""
    clientes = gestor.listar_clientes()
    if not clientes:
        print("No hay clientes.")
        return
    for c in clientes:
        saldo = gestor.obtener_saldo_deuda(c.id)
        print(
            f"  [{c.id[:8]}] {c.nombre} | {c.cedula_rif} | {c.telefono} | "
            f"deuda {formatear_moneda(saldo, Moneda.USD)}"
        )


def accion_registrar_abono(gestor: GestorClientes) -> None:
    """Registra un abono a la deuda de un cliente."""
    try:
        cliente = _seleccionar_cliente(gestor)
        monto = pedir_decimal("Monto")
        moneda = pedir_moneda("Moneda del abono")
        metodo = input(
            "Método (efectivo_usd/efectivo_bs/pago_movil/otro): "
        ).strip()
        if metodo not in METODOS_ABONO_VALIDOS:
            raise ValorInvalidoError(f"Método de pago inválido: {metodo}.")
        nota = input("Nota (Enter si ninguna): ").strip() or None
        abono = gestor.registrar_abono(cliente.id, monto, moneda, metodo, nota)
        print(f"OK: abono registrado ({formatear_moneda(abono.monto_usd, Moneda.USD)})")
    except (KlarisError, ValueError, ArithmeticError) as e:
        print(f"Error: {e}")
