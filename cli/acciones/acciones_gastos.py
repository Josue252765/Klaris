"""Acciones de CLI relacionadas con Gastos."""

from core.gastos import CategoriaGasto, GestorGastos
from core.moneda import Moneda
from cli.helpers import pedir_decimal, pedir_moneda
from utils.excepciones import KlarisError, ValorInvalidoError
from utils.formatos import formatear_moneda

_CATEGORIAS_GASTO = {
    "1": CategoriaGasto.MERCANCIA,
    "2": CategoriaGasto.SERVICIOS,
    "3": CategoriaGasto.SUELDOS,
    "4": CategoriaGasto.OTROS,
}


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
