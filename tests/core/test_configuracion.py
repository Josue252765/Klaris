"""Tests de core/configuracion.py: valores por defecto, persistencia y validación."""

from decimal import Decimal
from uuid import uuid4

import pytest

from core.configuracion import ConfiguracionNegocio, GestorConfiguracion
from core.moneda import Moneda
from utils.excepciones import ValorInvalidoError


class RepoConfiguracionMemoria:
    def __init__(self) -> None:
        self._configuracion: ConfiguracionNegocio | None = None

    def obtener(self) -> ConfiguracionNegocio | None:
        return self._configuracion

    def guardar(self, config: ConfiguracionNegocio) -> None:
        self._configuracion = config


def test_obtener_valores_por_defecto_sin_configuracion_guardada() -> None:
    repo = RepoConfiguracionMemoria()
    gestor = GestorConfiguracion(repo)
    config = gestor.obtener()
    assert config.nombre_negocio == "Mi Negocio"
    assert config.mensaje_pie == "¡Gracias por su compra!"
    assert config.moneda_default == Moneda.USD


def test_actualizar_persiste_y_obtener_lo_refleja() -> None:
    repo = RepoConfiguracionMemoria()
    gestor = GestorConfiguracion(repo)
    nueva = gestor.actualizar("Botica", "Gracias por confiar en nosotros", Moneda.USD)
    assert nueva.nombre_negocio == "Botica"
    assert nueva.mensaje_pie == "Gracias por confiar en nosotros"
    assert nueva.moneda_default == Moneda.USD
    assert repo.obtener() is nueva


def test_actualizar_nombre_vacio_lanza() -> None:
    repo = RepoConfiguracionMemoria()
    gestor = GestorConfiguracion(repo)
    with pytest.raises(ValorInvalidoError, match="nombre del negocio"):
        gestor.actualizar("", "Mensaje", Moneda.USD)


def test_actualizar_mensaje_vacio_lanza() -> None:
    repo = RepoConfiguracionMemoria()
    gestor = GestorConfiguracion(repo)
    with pytest.raises(ValorInvalidoError, match="mensaje de pie de ticket"):
        gestor.actualizar("Nombre", "", Moneda.USD)
