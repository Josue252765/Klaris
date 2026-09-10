"""Acciones de la CLI: una función por opción de menú, sin lógica de negocio."""

from datetime import date
from decimal import Decimal

from core.clientes import GestorClientes, METODOS_ABONO_VALIDOS
from core.devoluciones import GestorDevoluciones
from core.gastos import CategoriaGasto, GestorGastos
from core.inventario import GestorInventario
from core.moneda import Moneda
from core.producto import GestorProductos
from core.tasas import GestorTasas
from core.ventas import GestorVentas, Venta
from cli.helpers import (
    armar_carrito,
    imprimir_ticket,
    pedir_decimal,
    pedir_int,
    pedir_metodo_pago,
    pedir_moneda,
    pedir_monto_recibido,
    seleccionar_producto,
)
from utils.excepciones import KlarisError, ValorInvalidoError
from utils.formatos import formatear_fecha, formatear_moneda

_CATEGORIAS_GASTO = {
    "1": CategoriaGasto.MERCANCIA,
    "2": CategoriaGasto.SERVICIOS,
    "3": CategoriaGasto.SUELDOS,
    "4": CategoriaGasto.OTROS,
}


# --- Productos ---


def accion_crear_producto(gestor: GestorProductos) -> None:
    """Crea un producto pidiendo datos por teclado; imprime confirmación o error."""
    try:
        nombre = input("Nombre: ").strip()
        categoria = input("Categoría: ").strip()
        moneda_costo = pedir_moneda("Moneda del costo")
        costo = pedir_decimal("Costo unitario")
        margen = pedir_decimal("Margen de ganancia (%)")
        stock = pedir_int("Stock inicial")
        stock_min = pedir_int("Stock mínimo")
        unidad = input("Unidad de medida: ").strip()
        producto = gestor.crear(
            nombre=nombre, categoria=categoria, costo_unitario=costo,
            margen_ganancia=margen, stock_inicial=stock,
            stock_minimo=stock_min, unidad_medida=unidad,
            costo_moneda=moneda_costo,
        )
        print(f"OK: producto creado (id={producto.id})")
    except (KlarisError, ValueError, ArithmeticError) as e:
        print(f"Error: {e}")


def accion_listar_productos(gestor: GestorProductos) -> None:
    """Lista todos los productos activos con su stock."""
    productos = gestor.listar()
    if not productos:
        print("No hay productos.")
        return
    for p in productos:
        print(f"  [{p.codigo}] {p.nombre} | {p.categoria} | "
              f"costo {formatear_moneda(p.costo_unitario, Moneda.USD)} | "
              f"stock {p.stock_actual}/{p.stock_minimo} {p.unidad_medida}")


def accion_buscar_producto(gestor: GestorProductos) -> None:
    """Busca productos por nombre y muestra coincidencias."""
    try:
        texto = input("Texto a buscar: ").strip()
        resultados = gestor.buscar_por_nombre(texto)
        if not resultados:
            print("Sin coincidencias.")
            return
        for p in resultados:
            print(f"  [{p.codigo}] {p.nombre} | stock {p.stock_actual}")
    except KlarisError as e:
        print(f"Error: {e}")


def accion_editar_producto(gestor: GestorProductos) -> None:
    """Edita campos de un producto; Enter = mantener valor actual."""
    try:
        producto = seleccionar_producto(gestor)
        if producto is None:
            return
        print(f"Editando: {producto.nombre}")
        campos: dict[str, object] = {}
        costo_moneda = Moneda.USD
        nuevo = input(f"Nombre ({producto.nombre}): ").strip()
        if nuevo:
            campos["nombre"] = nuevo
        nuevo_costo = input(f"Costo unitario ({producto.costo_unitario}): ").strip()
        if nuevo_costo:
            costo_moneda = pedir_moneda("Moneda del nuevo costo")
            campos["costo_unitario"] = Decimal(nuevo_costo)
        nuevo_stock = input(f"Stock actual ({producto.stock_actual}): ").strip()
        if nuevo_stock:
            campos["stock_actual"] = int(nuevo_stock)
        if campos:
            gestor.actualizar(producto.id, costo_moneda=costo_moneda, **campos)
            print("OK: producto actualizado.")
        else:
            print("Sin cambios.")
    except (KlarisError, ValueError, ArithmeticError) as e:
        print(f"Error: {e}")


# --- Inventario ---


def accion_entrada_inventario(
    gestor_inventario: GestorInventario, gestor_productos: GestorProductos
) -> None:
    """Registra una entrada de stock pidiendo datos por teclado."""
    try:
        producto = seleccionar_producto(gestor_productos)
        if producto is None:
            return
        cantidad = pedir_int("Cantidad")
        motivo = input("Motivo: ").strip()
        movimiento = gestor_inventario.registrar_entrada(producto.id, cantidad, motivo)
        print(f"OK: entrada registrada (+{movimiento.cantidad})")
    except (KlarisError, ValueError) as e:
        print(f"Error: {e}")


def accion_salida_inventario(
    gestor_inventario: GestorInventario, gestor_productos: GestorProductos
) -> None:
    """Registra una salida de stock pidiendo datos por teclado."""
    try:
        producto = seleccionar_producto(gestor_productos)
        if producto is None:
            return
        cantidad = pedir_int("Cantidad")
        motivo = input("Motivo: ").strip()
        movimiento = gestor_inventario.registrar_salida(producto.id, cantidad, motivo)
        print(f"OK: salida registrada (-{movimiento.cantidad})")
    except (KlarisError, ValueError) as e:
        print(f"Error: {e}")


def accion_ajustar_stock(
    gestor_inventario: GestorInventario, gestor_productos: GestorProductos
) -> None:
    """Ajusta el stock a un valor exacto pidiendo datos por teclado."""
    try:
        producto = seleccionar_producto(gestor_productos)
        if producto is None:
            return
        nueva_cantidad = pedir_int("Nueva cantidad")
        motivo = input("Motivo: ").strip()
        movimiento = gestor_inventario.ajustar_stock(producto.id, nueva_cantidad, motivo)
        print(f"OK: stock ajustado a {movimiento.cantidad}")
    except (KlarisError, ValueError) as e:
        print(f"Error: {e}")


def accion_ver_stock_bajo(gestor: GestorInventario) -> None:
    """Muestra los productos con stock bajo o igual al mínimo."""
    productos = gestor.productos_stock_bajo()
    if not productos:
        print("No hay productos con stock bajo.")
        return
    print("Productos con stock bajo:")
    for p in productos:
        print(f"  [{p.id[:8]}] {p.nombre} | {p.stock_actual}/{p.stock_minimo}")


# --- Ventas ---


def accion_vender(
    gestor_ventas: GestorVentas,
    gestor_productos: GestorProductos,
    gestor_clientes: GestorClientes | None = None,
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
        imprimir_ticket(venta, gestor_productos)
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


# --- Gastos ---


def accion_registrar_gasto(gestor: GestorGastos) -> None:
    """Registra un gasto pidiendo categoría, descripción, monto y moneda."""
    try:
        print("Categoría: 1=MERCANCIA 2=SERVICIOS 3=SUELDOS 4=OTROS")
        cat_opcion = input("Opción: ").strip()
        if cat_opcion not in _CATEGORIAS_GASTO:
            raise ValorInvalidoError("Categoría inválida.")
        categoria = _CATEGORIAS_GASTO[cat_opcion]
        descripcion = input("Descripción: ").strip()
        monto = pedir_decimal("Monto")
        moneda = pedir_moneda("Moneda del gasto")
        gasto = gestor.registrar(categoria, descripcion, monto, moneda)
        print(f"OK: gasto registrado (id={gasto.id}, monto USD={gasto.monto})")
    except (KlarisError, ValueError, ArithmeticError) as e:
        print(f"Error: {e}")


def accion_listar_gastos(gestor: GestorGastos) -> None:
    """Lista todos los gastos registrados."""
    gastos = gestor.listar()
    if not gastos:
        print("No hay gastos.")
        return
    for g in gastos:
        print(f"  [{g.id[:8]}] {g.categoria.value} | {g.descripcion} | "
              f"{formatear_moneda(g.monto, Moneda.USD)}")


# --- Tasas ---


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


# --- Reporte ---


def accion_reporte_dia(
    gestor_ventas: GestorVentas, gestor_gastos: GestorGastos
) -> None:
    """Muestra ventas, gastos y ganancia neta de un rango de fechas."""
    try:
        respuesta = input("¿Fecha específica? (Enter para hoy): ").strip()
        if respuesta:
            desde = date.fromisoformat(respuesta)
            hasta_resp = input("¿Hasta qué fecha? (Enter = mismo día): ").strip()
            hasta = date.fromisoformat(hasta_resp) if hasta_resp else desde
        else:
            desde = hasta = date.today()
        ventas = gestor_ventas.listar(desde=desde, hasta=hasta)
        total_ventas = sum((v.total for v in ventas), Decimal("0"))
        print(f"\nVentas ({len(ventas)}): {formatear_moneda(total_ventas, Moneda.USD)}")
        for v in ventas:
            print(f"  [{v.id[:8]}] {formatear_moneda(v.total, Moneda.USD)}")
        gastos = gestor_gastos.listar(desde=desde, hasta=hasta)
        total_gastos = sum((g.monto for g in gastos), Decimal("0"))
        print(f"\nGastos ({len(gastos)}): {formatear_moneda(total_gastos, Moneda.USD)}")
        for g in gastos:
            print(f"  {g.descripcion}: {formatear_moneda(g.monto, Moneda.USD)}")
        ganancia = total_ventas - total_gastos
        print(f"\nGanancia neta: {formatear_moneda(ganancia, Moneda.USD)}")
    except (KlarisError, ValueError) as e:
        print(f"Error: {e}")


# --- Reportes ---


def accion_cierre_de_caja(generador) -> None:
    """Muestra el cierre de caja de una fecha o del día actual."""
    from core.moneda import Moneda
    try:
        respuesta = input("Fecha (YYYY-MM-DD) o Enter para hoy: ").strip()
        if respuesta:
            desde = date.fromisoformat(respuesta)
            hasta_resp = input("Hasta (YYYY-MM-DD) o Enter = mismo día: ").strip()
            hasta = date.fromisoformat(hasta_resp) if hasta_resp else desde
        else:
            desde = hasta = date.today()
        cierre = generador.cierre_de_caja(desde, hasta)
        print(f"\n--- CIERRE DE CAJA {formatear_fecha(desde)}"
              + (f" al {formatear_fecha(hasta)}" if hasta != desde else "") + " ---")
        print(f"  Ventas: {formatear_moneda(cierre.total_ventas_usd, Moneda.USD)}"
              + (f"  /  {formatear_moneda(cierre.total_ventas_bs, Moneda.BS)}"
                 if cierre.total_ventas_bs else ""))
        print("  Por método:")
        for d in cierre.desglose_pago:
            if d.cantidad_ventas > 0:
                print(f"    {d.metodo}: {formatear_moneda(d.total_usd, Moneda.USD)}"
                      f" ({d.cantidad_ventas} venta/s)")
        print(f"  Gastos: {formatear_moneda(cierre.total_gastos_usd, Moneda.USD)}"
              + (f"  /  {formatear_moneda(cierre.total_gastos_bs, Moneda.BS)}"
                 if cierre.total_gastos_bs else ""))
        signo = "+" if cierre.balance_neto_usd >= 0 else ""
        print(f"  Balance neto: {signo}{formatear_moneda(cierre.balance_neto_usd, Moneda.USD)}")
        print("-" * 40)
    except (KlarisError, ValueError) as e:
        print(f"Error: {e}")


def accion_top_productos(generador, repo_productos) -> None:
    """Muestra el ranking de productos más vendidos en cantidad."""
    try:
        limite_str = input("Cuántos productos mostrar (Enter = 5): ").strip()
        limite = int(limite_str) if limite_str else 5
        desde_str = input("Desde (YYYY-MM-DD) o Enter sin filtro: ").strip()
        hasta_str = input("Hasta (YYYY-MM-DD) o Enter sin filtro: ").strip()
        desde = date.fromisoformat(desde_str) if desde_str else None
        hasta = date.fromisoformat(hasta_str) if hasta_str else None
        ranking = generador.top_productos_vendidos(limite=limite, desde=desde, hasta=hasta)
        if not ranking:
            print("Sin ventas en el período.")
            return
        print("\n--- TOP PRODUCTOS VENDIDOS ---")
        for pos, r in enumerate(ranking, start=1):
            producto = repo_productos.obtener(r.producto_id)
            nombre = producto.nombre if producto else r.producto_id[:8]
            from core.moneda import Moneda
            print(f"  {pos}. {nombre} — {r.cantidad_total} uds"
                  f" — {formatear_moneda(r.monto_total_usd, Moneda.USD)}")
        print("-" * 40)
    except (KlarisError, ValueError) as e:
        print(f"Error: {e}")


# --- Clientes ---


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
