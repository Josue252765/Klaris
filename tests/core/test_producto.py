"""Tests de core/producto.py: entidad Producto y GestorProductos."""

from decimal import Decimal
from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from core.producto import GestorProductos, Producto
from utils.excepciones import ProductoNoEncontradoError, ValorInvalidoError


def _producto_valido(**sobrescribir: object) -> Producto:
    datos = {
        "id": "b04ab05a-0000-4000-8000-000000000001",
        "nombre": "Harina de maíz",
        "categoria": "Alimentos",
        "costo_unitario": Decimal("2.50"),
        "margen_ganancia": Decimal("30"),
        "stock_actual": 10,
        "stock_minimo": 2,
        "unidad_medida": "kg",
    }
    datos.update(sobrescribir)
    return Producto(**datos)


def test_creacion_con_id_uuid_valido() -> None:
    producto = Producto(
        id="b04ab05a-0000-4000-8000-000000000002",
        nombre="Azúcar",
        categoria="Alimentos",
        costo_unitario=Decimal("1.20"),
        margen_ganancia=Decimal("25"),
        stock_actual=5,
        stock_minimo=1,
        unidad_medida="kg",
    )
    UUID(producto.id)
    assert producto.id == "b04ab05a-0000-4000-8000-000000000002"


def test_activo_por_defecto_es_true() -> None:
    producto = _producto_valido()
    assert producto.activo is True


def test_nombre_vacio_lanza_valor_invalido() -> None:
    with pytest.raises(ValorInvalidoError):
        _producto_valido(nombre="   ")


def test_nombre_muy_largo_lanza_valor_invalido() -> None:
    with pytest.raises(ValorInvalidoError):
        _producto_valido(nombre="a" * 101)


def test_categoria_vacia_lanza_valor_invalido() -> None:
    with pytest.raises(ValorInvalidoError):
        _producto_valido(categoria="")


def test_costo_negativo_lanza_valor_invalido() -> None:
    with pytest.raises(ValorInvalidoError):
        _producto_valido(costo_unitario=Decimal("-1"))


def test_costo_float_es_rechazado() -> None:
    with pytest.raises(ValorInvalidoError):
        _producto_valido(costo_unitario=2.5)


def test_stock_actual_negativo_lanza_valor_invalido() -> None:
    with pytest.raises(ValorInvalidoError):
        _producto_valido(stock_actual=-1)


def test_stock_minimo_negativo_lanza_valor_invalido() -> None:
    with pytest.raises(ValorInvalidoError):
        _producto_valido(stock_minimo=-1)


class RepositorioEnMemoria:
    """Repositorio falso en memoria para aislar a GestorProductos del disco."""

    def __init__(self) -> None:
        self._datos: dict[str, Producto] = {}

    def guardar(self, producto: Producto) -> None:
        self._datos[producto.id] = producto

    def obtener(self, id: str) -> Producto | None:
        return self._datos.get(id)

    def listar(self) -> list[Producto]:
        return list(self._datos.values())

    def actualizar(self, producto: Producto) -> None:
        self._datos[producto.id] = producto


@pytest.fixture()
def gestor() -> GestorProductos:
    return GestorProductos(RepositorioEnMemoria())


def test_crear_guarda_producto_con_uuid(gestor: GestorProductos) -> None:
    producto = gestor.crear(
        nombre="Aceite",
        categoria="Alimentos",
        costo_unitario=Decimal("4.00"),
        margen_ganancia=Decimal("30"),
        stock_inicial=3,
        stock_minimo=1,
        unidad_medida="litro",
    )
    UUID(producto.id)
    assert gestor.obtener(producto.id) == producto


def test_obtener_inexistente_lanza_no_encontrado(gestor: GestorProductos) -> None:
    with pytest.raises(ProductoNoEncontradoError):
        gestor.obtener("inexistente")


def test_actualizar_cambia_campos(gestor: GestorProductos) -> None:
    producto = gestor.crear(
        nombre="Sal",
        categoria="Alimentos",
        costo_unitario=Decimal("0.50"),
        margen_ganancia=Decimal("20"),
        stock_inicial=8,
        stock_minimo=2,
        unidad_medida="kg",
    )
    actualizado = gestor.actualizar(producto.id, nombre="Sal fina")
    assert actualizado.nombre == "Sal fina"
    assert gestor.obtener(producto.id).nombre == "Sal fina"


def test_id_inmutable_por_estructura() -> None:
    producto = _producto_valido()
    with pytest.raises(FrozenInstanceError):
        producto.id = "otro-id"


def test_desactivar_marca_inactivo(gestor: GestorProductos) -> None:
    producto = gestor.crear(
        nombre="Pan",
        categoria="Panadería",
        costo_unitario=Decimal("1.00"),
        margen_ganancia=Decimal("30"),
        stock_inicial=4,
        stock_minimo=1,
        unidad_medida="unidad",
    )
    gestor.desactivar(producto.id)
    assert gestor.obtener(producto.id).activo is False


def test_listar_filtra_inactivos(gestor: GestorProductos) -> None:
    activo = gestor.crear(
        nombre="Pan",
        categoria="Panadería",
        costo_unitario=Decimal("1.00"),
        margen_ganancia=Decimal("30"),
        stock_inicial=4,
        stock_minimo=1,
        unidad_medida="unidad",
    )
    inactivo = gestor.crear(
        nombre="Torta",
        categoria="Panadería",
        costo_unitario=Decimal("5.00"),
        margen_ganancia=Decimal("30"),
        stock_inicial=1,
        stock_minimo=1,
        unidad_medida="unidad",
    )
    gestor.desactivar(inactivo.id)
    assert gestor.listar() == [activo]
    assert {p.id for p in gestor.listar(solo_activos=False)} == {activo.id, inactivo.id}


def test_buscar_por_nombre_ignora_mayusculas(gestor: GestorProductos) -> None:
    gestor.crear(
        nombre="Harina de maíz",
        categoria="Alimentos",
        costo_unitario=Decimal("2.50"),
        margen_ganancia=Decimal("30"),
        stock_inicial=5,
        stock_minimo=1,
        unidad_medida="kg",
    )
    resultado = gestor.buscar_por_nombre("HARINA")
    assert len(resultado) == 1
    assert resultado[0].nombre == "Harina de maíz"