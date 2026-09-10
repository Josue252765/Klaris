"""Tests de integración end-to-end con repositorios JSON reales en tmp_path."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from config.settings import Settings
from core.gastos import CategoriaGasto, GestorGastos
from core.inventario import GestorInventario
from core.moneda import Moneda
from core.producto import GestorProductos
from core.tasas import GestorTasas
from core.ventas import Carrito, GestorVentas
from persistence.repositorios import (
    RepositorioGastosJSON,
    RepositorioMovimientosJSON,
    RepositorioProductosJSON,
    RepositorioTasaJSON,
    RepositorioVentasJSON,
)
from utils.excepciones import KlarisError, StockInsuficienteError, ValorInvalidoError


def _infra(tmp_path):
    """Crea Settings + repos + gestores apuntando a tmp_path."""
    config = Settings(directorio_datos=tmp_path)
    repo_prod = RepositorioProductosJSON(config.ruta_productos())
    repo_mov = RepositorioMovimientosJSON(config.ruta_movimientos())
    repo_ventas = RepositorioVentasJSON(config.ruta_ventas())
    repo_gastos = RepositorioGastosJSON(config.ruta_gastos())
    repo_tasas = RepositorioTasaJSON(config.ruta_tasas())

    gestor_tasas = GestorTasas(repo_tasas)
    gestor_prod = GestorProductos(repo_prod, repo_tasas)
    gestor_inv = GestorInventario(repo_prod, repo_mov)
    gestor_ventas = GestorVentas(gestor_inv, repo_prod, repo_ventas, repo_tasas)
    gestor_gastos = GestorGastos(repo_gastos, repo_tasas)
    return gestor_prod, gestor_inv, gestor_ventas, gestor_gastos, gestor_tasas


# === ESCENARIO 1: Día de negocio mixto ===


def test_dia_mixto_completo(tmp_path) -> None:
    g_prod, g_inv, g_ventas, g_gastos, g_tasas = _infra(tmp_path)

    # Guardar tasa antes de crear producto con costo en BS
    g_tasas.actualizar(Decimal("40"), Decimal("42"))

    # 3 productos: USD, BS (convierte), margen negativo
    p_usd = g_prod.crear(
        nombre="Aceite", categoria="Alimentos",
        costo_unitario=Decimal("4.00"), margen_ganancia=Decimal("30"),
        stock_inicial=0, stock_minimo=2, unidad_medida="litro",
    )
    p_bs = g_prod.crear(
        nombre="Harina", categoria="Alimentos",
        costo_unitario=Decimal("100"), margen_ganancia=Decimal("30"),
        stock_inicial=0, stock_minimo=2, unidad_medida="kg",
        costo_moneda=Moneda.BS,
    )
    p_neg = g_prod.crear(
        nombre="Promo", categoria="Varios",
        costo_unitario=Decimal("10"), margen_ganancia=Decimal("-20"),
        stock_inicial=0, stock_minimo=1, unidad_medida="unidad",
    )

    # Verificar conversión BS→USD
    assert p_bs.costo_unitario == Decimal("2.50")
    # Verificar margen negativo permitido
    assert p_neg.margen_ganancia == Decimal("-20")

    # Entradas de inventario
    g_inv.registrar_entrada(p_usd.id, 20, "compra")
    g_inv.registrar_entrada(p_bs.id, 30, "compra")
    g_inv.registrar_entrada(p_neg.id, 10, "compra")

    # Venta 1: pagada en USD
    carrito1 = Carrito()
    carrito1.agregar_item(g_prod.obtener(p_usd.id), 3)
    venta1 = g_ventas.cerrar_venta(carrito1, Moneda.USD, "efectivo_usd")
    assert venta1.total == Decimal("15.60")  # 4.00 * 1.30 * 3

    # Venta 2: pagada en BS con vuelto exacto
    carrito2 = Carrito()
    carrito2.agregar_item(g_prod.obtener(p_bs.id), 2)
    total_bs_esperado = Decimal("6.50") * Decimal("42")  # 273.00
    venta2 = g_ventas.cerrar_venta(
        carrito2, Moneda.USD, "efectivo_bs",
        moneda_pago=Moneda.BS, monto_recibido_bs=total_bs_esperado,
    )
    assert venta2.total_bs == Decimal("273.00")
    assert venta2.vuelto_bs == Decimal("0.00")

    # Venta 3: BS con pago insuficiente — debe fallar sin descontar stock
    carrito3 = Carrito()
    carrito3.agregar_item(g_prod.obtener(p_neg.id), 2)
    stock_antes = g_prod.obtener(p_neg.id).stock_actual
    with pytest.raises(ValorInvalidoError):
        g_ventas.cerrar_venta(
            carrito3, Moneda.USD, "efectivo_bs",
            moneda_pago=Moneda.BS, monto_recibido_bs=Decimal("1"),
        )
    assert g_prod.obtener(p_neg.id).stock_actual == stock_antes

    # 3 gastos: USD, BS, monto negativo (falla)
    g_gastos.registrar(CategoriaGasto.MERCANCIA, "Bolsas", Decimal("5"), Moneda.USD)
    g_gastos.registrar(CategoriaGasto.SERVICIOS, "Luz", Decimal("840"), Moneda.BS)
    with pytest.raises(ValorInvalidoError):
        g_gastos.registrar(CategoriaGasto.OTROS, "x", Decimal("-1"), Moneda.USD)

    # Reporte del día
    hoy = date.today()
    ventas = g_ventas.listar(desde=hoy, hasta=hoy)
    gastos = g_gastos.listar(desde=hoy, hasta=hoy)
    assert len(ventas) == 2
    assert len(gastos) == 2

    total_ventas = sum((v.total for v in ventas), Decimal("0"))
    total_gastos = g_gastos.total_periodo(hoy, hoy)
    ganancia = total_ventas - total_gastos
    # 15.60 + 6.50 = 22.10 ventas; 5 + 20.00 (840/42) = 25.00 gastos
    assert total_ventas == Decimal("22.10")
    assert total_gastos == Decimal("25.00")
    assert ganancia == Decimal("-2.90")

    # Stock final
    assert g_prod.obtener(p_usd.id).stock_actual == 17  # 20 - 3
    assert g_prod.obtener(p_bs.id).stock_actual == 28   # 30 - 2
    assert g_prod.obtener(p_neg.id).stock_actual == 10  # no se vendió


# === ESCENARIO 2: Casos límite ===


def test_vender_mas_de_stock_falla_sin_descontar(tmp_path) -> None:
    g_prod, g_inv, g_ventas, _, _ = _infra(tmp_path)
    p = g_prod.crear(
        nombre="Sal", categoria="Alimentos",
        costo_unitario=Decimal("1"), margen_ganancia=Decimal("20"),
        stock_inicial=5, stock_minimo=1, unidad_medida="kg",
    )
    carrito = Carrito()
    carrito.agregar_item(p, 3)

    # Simula que el stock cambió entre armar el carrito y cerrar la venta.
    g_inv.ajustar_stock(p.id, 1, "simular cambio externo")

    with pytest.raises(StockInsuficienteError):
        g_ventas.cerrar_venta(carrito, Moneda.USD, "efectivo_usd")

    assert g_prod.obtener(p.id).stock_actual == 1


def test_actualizar_tasa_dos_veces_mantiene_ultima(tmp_path) -> None:
    _, _, _, _, g_tasas = _infra(tmp_path)
    g_tasas.actualizar(Decimal("40"), Decimal("42"))
    g_tasas.actualizar(Decimal("45"), Decimal("48"))
    tasa = g_tasas.obtener_actual()
    assert tasa is not None
    assert tasa.tasa_referencial == Decimal("45")
    assert tasa.tasa_diaria == Decimal("48")


def test_reporte_rango_vacio_ganancia_cero(tmp_path) -> None:
    _, _, g_ventas, g_gastos, _ = _infra(tmp_path)
    futuro = date.today() + timedelta(days=100)
    ventas = g_ventas.listar(desde=futuro, hasta=futuro)
    gastos = g_gastos.listar(desde=futuro, hasta=futuro)
    assert ventas == []
    assert gastos == []
    total_gastos = g_gastos.total_periodo(futuro, futuro)
    assert total_gastos == Decimal("0")


def test_buscar_producto_inexistente_devuelve_vacio(tmp_path) -> None:
    g_prod, _, _, _, _ = _infra(tmp_path)
    g_prod.crear(
        nombre="Aceite", categoria="Alimentos",
        costo_unitario=Decimal("4"), margen_ganancia=Decimal("30"),
        stock_inicial=1, stock_minimo=1, unidad_medida="litro",
    )
    resultados = g_prod.buscar_por_nombre("xyz")
    assert resultados == []
