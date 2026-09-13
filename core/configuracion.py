"""Datos y gestión de configuración del negocio para tickets y personalización."""

from dataclasses import dataclass
from typing import Protocol

from core.moneda import Moneda
from utils.excepciones import ValorInvalidoError
from utils.validadores import validar_texto_no_vacio


@dataclass(frozen=True)
class ConfiguracionNegocio:
    """Datos de personalización del negocio para tickets y encabezados."""

    nombre_negocio: str
    mensaje_pie: str
    moneda_default: Moneda


class RepositorioConfiguracion(Protocol):
    """Contrato de persistencia de la configuración del negocio."""

    def obtener(self) -> ConfiguracionNegocio | None: ...

    def guardar(self, config: ConfiguracionNegocio) -> None: ...


_VALOR_POR_DEFECTO_NOMBRE = "Mi Negocio"
_VALOR_POR_DEFECTO_MENSAJE = "¡Gracias por su compra!"
_VALOR_POR_DEFECTO_MONEDA = Moneda.USD


class GestorConfiguracion:
    """Orquesta la lectura y actualización de la configuración del negocio."""

    def __init__(self, repositorio: RepositorioConfiguracion) -> None:
        self._repositorio = repositorio

    def obtener(self) -> ConfiguracionNegocio:
        """Devuelve la configuración guardada o los valores por defecto."""
        config = self._repositorio.obtener()
        if config is not None:
            return config
        return ConfiguracionNegocio(
            nombre_negocio=_VALOR_POR_DEFECTO_NOMBRE,
            mensaje_pie=_VALOR_POR_DEFECTO_MENSAJE,
            moneda_default=_VALOR_POR_DEFECTO_MONEDA,
        )

    def actualizar(
        self,
        nombre_negocio: str,
        mensaje_pie: str,
        moneda_default: Moneda,
    ) -> ConfiguracionNegocio:
        """Valida campos no vacíos y persiste la nueva configuración."""
        nombre = validar_texto_no_vacio(nombre_negocio, "nombre del negocio")
        mensaje = validar_texto_no_vacio(mensaje_pie, "mensaje de pie de ticket")
        config = ConfiguracionNegocio(
            nombre_negocio=nombre,
            mensaje_pie=mensaje,
            moneda_default=moneda_default,
        )
        self._repositorio.guardar(config)
        return config
