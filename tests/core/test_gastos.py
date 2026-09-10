"""Tests de core/gastos.py: Gasto y GestorGastos con repositorio en memoria."""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from core.gastos import CategoriaGasto, Gasto, GestorGastos
from core.moneda import Moneda, TasaCambio
from utils.excepciones import MonedaInvalidaError, ValorInvalidoError


class RepoGastosMemoria:
    def __init__(self) -> None:
        self._gastos: list[Gasto] = []

    def guardar(self, gasto: Gasto) -> None:
        self._gastos.append(gasto)

    def listar(self) -> list[Gasto]:
        return list(self._gastos)


class RepoTasaMemoria:
    def __init__(self, tasa: TasaCambio | None = None) -> None:
        self._tasa = tasa

    def obtener_actual(self) -> TasaCambio | None:
        return self._tasa


def _tasa_diaria_42() -> TasaCambio:
    return TasaCambio(
        tasa_referencial=Decimal("40"),
        tasa_referencial_fecha=date(2026, 9, 9),
        tasa_diaria=Decimal("42"),
        tasa_diaria_fecha=date(2026, 9, 9),
    )


@pytest.fixture()
def gestor() -> GestorGastos:
    return GestorGastos(RepoGastosMemoria())


def _fecha(dias_atras: int) -> datetime:
    return datetime.now() - timedelta(days=dias_atras)


def test_registrar_gasto_exitoso(gestor: GestorGastos) -> None:
    gasto = gestor.registrar(
        CategoriaGasto.MERCANCIA, "Compra de harina", Decimal("50.00"), Moneda.USD
    )
    assert gasto.categoria == CategoriaGasto.MERCANCIA
    assert gasto.descripcion == "Compra de harina"
    assert gasto.monto == Decimal("50.00")
    assert gasto.moneda == Moneda.USD
    assert gasto.fecha is not None


def test_registrar_monto_cero_lanza(gestor: GestorGastos) -> None:
    with pytest.raises(ValorInvalidoError):
        gestor.registrar(CategoriaGasto.OTROS, "x", Decimal("0"), Moneda.USD)


def test_registrar_monto_negativo_lanza(gestor: GestorGastos) -> None:
    with pytest.raises(ValorInvalidoError):
        gestor.registrar(CategoriaGasto.OTROS, "x", Decimal("-10"), Moneda.USD)


def test_registrar_monto_float_rechazado(gestor: GestorGastos) -> None:
    with pytest.raises(ValorInvalidoError):
        gestor.registrar(CategoriaGasto.OTROS, "x", 50.0, Moneda.USD)


def test_registrar_descripcion_vacia_lanza(gestor: GestorGastos) -> None:
    with pytest.raises(ValorInvalidoError):
        gestor.registrar(CategoriaGasto.OTROS, "   ", Decimal("10"), Moneda.USD)


def test_registrar_moneda_invalida_lanza(gestor: GestorGastos) -> None:
    with pytest.raises(MonedaInvalidaError):
        gestor.registrar(CategoriaGasto.OTROS, "x", Decimal("10"), "USD")


def test_listar_sin_filtros(gestor: GestorGastos) -> None:
    gestor.registrar(CategoriaGasto.MERCANCIA, "a", Decimal("10"), Moneda.USD)
    gestor.registrar(CategoriaGasto.SERVICIOS, "b", Decimal("20"), Moneda.USD)
    assert len(gestor.listar()) == 2


def test_listar_filtrar_por_categoria(gestor: GestorGastos) -> None:
    gestor.registrar(CategoriaGasto.MERCANCIA, "a", Decimal("10"), Moneda.USD)
    gestor.registrar(CategoriaGasto.SERVICIOS, "b", Decimal("20"), Moneda.USD)
    gestor.registrar(CategoriaGasto.MERCANCIA, "c", Decimal("5"), Moneda.USD)
    resultado = gestor.listar(categoria=CategoriaGasto.MERCANCIA)
    assert len(resultado) == 2
    assert all(g.categoria == CategoriaGasto.MERCANCIA for g in resultado)


def test_listar_filtrar_por_fecha(gestor: GestorGastos) -> None:
    repo = RepoGastosMemoria()
    gestor_con_fechas = GestorGastos(repo)
    g1 = Gasto(
        id="1",
        categoria=CategoriaGasto.MERCANCIA,
        descripcion="a",
        monto=Decimal("10"),
        moneda=Moneda.USD,
        fecha=_fecha(10),
    )
    g2 = Gasto(
        id="2",
        categoria=CategoriaGasto.MERCANCIA,
        descripcion="b",
        monto=Decimal("20"),
        moneda=Moneda.USD,
        fecha=_fecha(1),
    )
    repo.guardar(g1)
    repo.guardar(g2)
    desde = date.today() - timedelta(days=5)
    resultado = gestor_con_fechas.listar(desde=desde)
    assert len(resultado) == 1
    assert resultado[0].id == "2"


def test_total_periodo_suma_usd(gestor: GestorGastos) -> None:
    gestor.registrar(CategoriaGasto.MERCANCIA, "a", Decimal("10"), Moneda.USD)
    gestor.registrar(CategoriaGasto.SERVICIOS, "b", Decimal("20.50"), Moneda.USD)
    total = gestor.total_periodo(date.today() - timedelta(days=1), date.today() + timedelta(days=1))
    assert total == Decimal("30.50")


def test_gasto_bs_convierte_y_guarda_trazabilidad() -> None:
    repo_gastos = RepoGastosMemoria()
    repo_tasa = RepoTasaMemoria(_tasa_diaria_42())
    gestor = GestorGastos(repo_gastos, repo_tasa)
    gasto = gestor.registrar(
        CategoriaGasto.MERCANCIA, "Compra", Decimal("420"), Moneda.BS
    )
    assert gasto.monto == Decimal("10.00")
    assert gasto.monto_original == Decimal("420")
    assert gasto.moneda_original == Moneda.BS
    assert gasto.tasa_usada == Decimal("42")


def test_gasto_usd_guarda_origen_sin_tasa() -> None:
    repo_gastos = RepoGastosMemoria()
    gestor = GestorGastos(repo_gastos)
    gasto = gestor.registrar(
        CategoriaGasto.MERCANCIA, "Compra", Decimal("50"), Moneda.USD
    )
    assert gasto.monto_original == Decimal("50")
    assert gasto.moneda_original == Moneda.USD
    assert gasto.tasa_usada is None


def test_total_periodo_suma_mixto_sin_lanzar() -> None:
    repo_gastos = RepoGastosMemoria()
    repo_tasa = RepoTasaMemoria(_tasa_diaria_42())
    gestor = GestorGastos(repo_gastos, repo_tasa)
    gestor.registrar(CategoriaGasto.MERCANCIA, "a", Decimal("10"), Moneda.USD)
    gestor.registrar(CategoriaGasto.MERCANCIA, "b", Decimal("420"), Moneda.BS)
    total = gestor.total_periodo(
        date.today() - timedelta(days=1), date.today() + timedelta(days=1)
    )
    assert total == Decimal("20.00")


def test_gasto_bs_sin_tasa_lanza() -> None:
    repo_gastos = RepoGastosMemoria()
    repo_tasa = RepoTasaMemoria(None)
    gestor = GestorGastos(repo_gastos, repo_tasa)
    with pytest.raises(MonedaInvalidaError):
        gestor.registrar(CategoriaGasto.MERCANCIA, "a", Decimal("100"), Moneda.BS)


def test_total_periodo_rango_vacio_devuelve_cero(gestor: GestorGastos) -> None:
    gestor.registrar(CategoriaGasto.MERCANCIA, "a", Decimal("10"), Moneda.USD)
    total = gestor.total_periodo(
        date.today() + timedelta(days=10), date.today() + timedelta(days=20)
    )
    assert total == Decimal("0")