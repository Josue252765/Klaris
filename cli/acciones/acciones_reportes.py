"""Acciones de CLI relacionadas con Reportes y Cierre de Caja."""

from datetime import date
from decimal import Decimal

from core.gastos import GestorGastos
from core.moneda import Moneda
from core.ventas import GestorVentas
from utils.excepciones import KlarisError
from utils.formatos import formatear_fecha, formatear_moneda


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


def accion_cierre_de_caja(generador) -> None:
    """Muestra el cierre de caja de una fecha o del día actual."""
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
            print(f"  {pos}. {nombre} — {r.cantidad_total} uds"
                  f" — {formatear_moneda(r.monto_total_usd, Moneda.USD)}")
        print("-" * 40)
    except (KlarisError, ValueError) as e:
        print(f"Error: {e}")
