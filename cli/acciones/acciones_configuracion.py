"""Acciones de CLI relacionadas con Configuración del Negocio."""

from core.configuracion import GestorConfiguracion, ConfiguracionNegocio
from core.moneda import Moneda
from cli.helpers import pedir_moneda
from utils.excepciones import KlarisError


def accion_editar_configuracion(gestor_configuracion: GestorConfiguracion) -> None:
    """Muestra valores actuales y permite actualizar nombre, pie y moneda por defecto."""
    try:
        config = gestor_configuracion.obtener()
        print(f"Nombre actual: {config.nombre_negocio}")
        print(f"Mensaje pie actual: {config.mensaje_pie}")
        print(f"Moneda por defecto actual: {config.moneda_default.value}")
        nombre = input(f"Nuevo nombre ({config.nombre_negocio}): ").strip()
        nombre = nombre or config.nombre_negocio
        mensaje = input(f"Nuevo mensaje pie ({config.mensaje_pie}): ").strip()
        mensaje = mensaje or config.mensaje_pie
        moneda_input = input(f"Moneda por defecto (USD/BS, actual {config.moneda_default.value}): ").strip()
        moneda = moneda_input if moneda_input else config.moneda_default.value
        if moneda.upper() == "BS" or moneda == "BS":
            moneda = Moneda.BS
        else:
            moneda = Moneda.USD
        if moneda_input and moneda_input.upper() not in ("USD", "BS"):
            raise ValueError("Moneda inválida.")
        nueva = gestor_configuracion.actualizar(nombre, mensaje, moneda)
        print(f"OK: configuración actualizada")
        print(f"  Nombre: {nueva.nombre_negocio}")
        print(f"  Mensaje pie: {nueva.mensaje_pie}")
        print(f"  Moneda por defecto: {nueva.moneda_default.value}")
    except (KlarisError, ValueError) as e:
        print(f"Error: {e}")
