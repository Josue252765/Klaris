"""Tests de core/reportes.py: CierreCaja y top_productos con repositorios en memoria."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from core.gastos import CategoriaGasto, Gasto, GestorGastos
from core.inventario import GestorInventario, MovimientoStock
from core.moneda import Moneda, TasaCambio
from core.producto import Producto
from core.reportes import CierreCaja, GeneradorReportes, ProductoRanking
from core.ventas import GestorVentas, ItemCarrito, Venta


# ---------------------------------------------------------------------------
# Repos en memoria
# ---------------------------------------------------------------------------

class RepoProductosMemoria:
    def __init__(self) -> None:
        self._datos: dict[str, Producto] = {}

    def guardar(self, p: Producto) -> None:
        self._datos[p.id] = p

    def obtener(self, id: str) -> Producto | None:
        return self._datos.get(id)

    def listar(self) -> list[Producto]:
        return list(self._datos.values())

    def actualizar(self, p: Producto) -> None:
        self._datos[p.id] = p


class RepoMovimientosMemoria:
    def __init__(self) -> None:
        self._items: list[MovimientoStock] = []

    def guardar(self, m: MovimientoStock) -> None:
        self._items.append(m)


class RepoVentasMemoria:
    def __init__(self) -> None:
        self._items: list[Venta] = []

    def guardar(self, v: Venta) -> None:
        self._items.append(v)

    def listar(self) -> list[Venta]:
        return list(self._items)

    def actualizar(self, v: Venta) -> None:
        for i, actual in enumerate(self._items):
            if actual.id == v.id:
                self._items[i] = v
                return


class RepoGastosMemoria:
    def __init__(self) -> None:
        self._items: list[Gasto] = []

    def guardar(self, g: Gasto) -> None:
        self._items.append(g)

    def listar(self) -> list[Gasto]:
        return list(self._items)


class RepoTasaMemoria:
    def __init__(self, tasa: TasaCambio | None = None) -> None:
        self._tasa = tasa

    def obtener_actual(self) -> TasaCambio | None:
        return self._tasa

    def guardar(self, tasa: TasaCambio) -> None:
        self._tasa = tasa


# ---------------------------------------------------------------------------
# Helpers de construcción
# ---------------------------------------------------------------------------

def _tasa(ref: str = "36.00", diaria: str = "38.00") -> TasaCambio:
    return TasaCambio(
        tasa_referencial=Decimal(ref),
        tasa_referencial_fecha=date.today(),
        tasa_diaria=Decimal(diaria),
        tasa_diaria_fecha=date.today(),
    )


def _producto(nombre: str = "Harina", costo: str = "2.50", stock: int = 10) -> Producto:
    return Producto(
        id=str(uuid4()),
        nombre=nombre,
        categoria="Alimentos",
        costo_unitario=Decimal(costo),
        margen_ganancia=Decimal("20"),
        stock_actual=stock,
        stock_minimo=2,
        unidad_medida="kg",
        codigo="ALI-0001",
    )


def _venta(
    items: list[ItemCarrito],
    total: str,
    metodo: str = "efectivo_usd",
    fecha: date | None = None,
    total_bs: str | None = None,
    tasa_usada: str | None = None,
    monto_recibido_bs: str | None = None,
    vuelto_bs: str | None = None,
) -> Venta:
    dia = fecha or date.today()
    return Venta(
        id=str(uuid4()),
        items=items,
        total=Decimal(total),
        moneda=Moneda.USD,
        metodo_pago=metodo,
        fecha=datetime(dia.year, dia.month, dia.day, 10, 0),
        total_bs=Decimal(total_bs) if total_bs else None,
        tasa_usada=Decimal(tasa_usada) if tasa_usada else None,
        monto_recibido_bs=Decimal(monto_recibido_bs) if monto_recibido_bs else None,
        vuelto_bs=Decimal(vuelto_bs) if vuelto_bs else None,
    )


def _gasto(monto: str, moneda: Moneda = Moneda.USD, fecha: date | None = None) -> Gasto:
    dia = fecha or date.today()
    return Gasto(
        id=str(uuid4()),
        categoria=CategoriaGasto.MERCANCIA,
        descripcion="Compra mercancía",
        monto=Decimal(monto),
        moneda=Moneda.USD,
        fecha=datetime(dia.year, dia.month, dia.day, 9, 0),
    )


def _generador(tasa: TasaCambio | None = None) -> tuple[GeneradorReportes, RepoVentasMemoria, RepoGastosMemoria]:
    repo_prod = RepoProductosMemoria()
    repo_mov = RepoMovimientosMemoria()
    repo_ventas = RepoVentasMemoria()
    repo_gastos = RepoGastosMemoria()
    repo_tasa = RepoTasaMemoria(tasa)

    gestor_inv = GestorInventario(repo_prod, repo_mov)
    gestor_ventas = GestorVentas(gestor_inv, repo_prod, repo_ventas, repo_tasa)
    gestor_gastos = GestorGastos(repo_gastos, repo_tasa)
    gen = GeneradorReportes(gestor_ventas, gestor_gastos, repo_tasa)
    return gen, repo_ventas, repo_gastos


# ---------------------------------------------------------------------------
# Tests: cierre_de_caja
# ---------------------------------------------------------------------------

def test_cierre_dia_sin_ventas_ni_gastos():
    gen, _, _ = _generador()
    cierre = gen.cierre_de_caja(date.today())
    assert cierre.total_ventas_usd == Decimal("0")
    assert cierre.total_gastos_usd == Decimal("0")
    assert cierre.balance_neto_usd == Decimal("0")
    assert len(cierre.desglose_pago) == 5


def test_cierre_con_una_venta_efectivo_usd():
    gen, repo_v, _ = _generador(_tasa())
    pid = str(uuid4())
    item = ItemCarrito(producto_id=pid, cantidad=2, precio_unitario=Decimal("3.25"))
    repo_v.guardar(_venta([item], "6.50", metodo="efectivo_usd"))

    cierre = gen.cierre_de_caja(date.today())

    assert cierre.total_ventas_usd == Decimal("6.50")
    assert cierre.balance_neto_usd == Decimal("6.50")
    efectivo_usd = next(d for d in cierre.desglose_pago if d.metodo == "efectivo_usd")
    assert efectivo_usd.total_usd == Decimal("6.50")
    assert efectivo_usd.cantidad_ventas == 1


def test_cierre_desglose_multiples_metodos():
    gen, repo_v, _ = _generador(_tasa())
    pid = str(uuid4())
    item = ItemCarrito(producto_id=pid, cantidad=1, precio_unitario=Decimal("5.00"))
    repo_v.guardar(_venta([item], "5.00", metodo="efectivo_usd"))
    repo_v.guardar(_venta([item], "5.00", metodo="pago_movil"))
    repo_v.guardar(_venta([item], "5.00", metodo="efectivo_bs"))

    cierre = gen.cierre_de_caja(date.today())

    assert cierre.total_ventas_usd == Decimal("15.00")
    metodos = {d.metodo: d for d in cierre.desglose_pago}
    assert metodos["efectivo_usd"].cantidad_ventas == 1
    assert metodos["pago_movil"].cantidad_ventas == 1
    assert metodos["efectivo_bs"].cantidad_ventas == 1
    assert metodos["otro"].cantidad_ventas == 0


def test_cierre_con_gastos_resta_del_balance():
    gen, repo_v, repo_g = _generador(_tasa())
    pid = str(uuid4())
    item = ItemCarrito(producto_id=pid, cantidad=1, precio_unitario=Decimal("10.00"))
    repo_v.guardar(_venta([item], "10.00"))
    repo_g.guardar(_gasto("4.00"))

    cierre = gen.cierre_de_caja(date.today())

    assert cierre.total_ventas_usd == Decimal("10.00")
    assert cierre.total_gastos_usd == Decimal("4.00")
    assert cierre.balance_neto_usd == Decimal("6.00")


def test_cierre_balance_negativo_cuando_gastos_superan_ventas():
    gen, repo_v, repo_g = _generador(_tasa())
    pid = str(uuid4())
    item = ItemCarrito(producto_id=pid, cantidad=1, precio_unitario=Decimal("5.00"))
    repo_v.guardar(_venta([item], "5.00"))
    repo_g.guardar(_gasto("20.00"))

    cierre = gen.cierre_de_caja(date.today())
    assert cierre.balance_neto_usd == Decimal("-15.00")


def test_cierre_total_bs_calculado_con_tasa_diaria():
    t = _tasa(diaria="40.00")
    gen, repo_v, _ = _generador(t)
    pid = str(uuid4())
    item = ItemCarrito(producto_id=pid, cantidad=1, precio_unitario=Decimal("10.00"))
    repo_v.guardar(_venta([item], "10.00"))

    cierre = gen.cierre_de_caja(date.today())
    assert cierre.total_ventas_bs == Decimal("400.00")


def test_cierre_sin_tasa_devuelve_bs_cero():
    gen, repo_v, _ = _generador(tasa=None)
    pid = str(uuid4())
    item = ItemCarrito(producto_id=pid, cantidad=1, precio_unitario=Decimal("5.00"))
    repo_v.guardar(_venta([item], "5.00"))

    cierre = gen.cierre_de_caja(date.today())
    assert cierre.total_ventas_bs == Decimal("0")
    assert cierre.total_gastos_bs == Decimal("0")


def test_cierre_rango_de_fechas_excluye_otros_dias():
    gen, repo_v, _ = _generador(_tasa())
    hoy = date.today()
    ayer = date(hoy.year, hoy.month, hoy.day)

    pid = str(uuid4())
    item = ItemCarrito(producto_id=pid, cantidad=1, precio_unitario=Decimal("7.00"))
    repo_v.guardar(_venta([item], "7.00", fecha=hoy))
    # Venta en fecha futura — no debe incluirse
    futuro = date(hoy.year + 1, hoy.month, hoy.day)
    repo_v.guardar(_venta([item], "99.00", fecha=futuro))

    cierre = gen.cierre_de_caja(hoy)
    assert cierre.total_ventas_usd == Decimal("7.00")


def test_cierre_fecha_hasta_diferente_a_desde():
    gen, repo_v, _ = _generador(_tasa())
    hoy = date.today()
    futuro = date(hoy.year, hoy.month, hoy.day)
    pid = str(uuid4())
    item = ItemCarrito(producto_id=pid, cantidad=1, precio_unitario=Decimal("3.00"))
    repo_v.guardar(_venta([item], "3.00", fecha=hoy))
    repo_v.guardar(_venta([item], "3.00", fecha=hoy))

    cierre = gen.cierre_de_caja(hoy, futuro)
    assert cierre.total_ventas_usd == Decimal("6.00")
    assert cierre.fecha_desde == hoy
    assert cierre.fecha_hasta == futuro


# ---------------------------------------------------------------------------
# Tests: top_productos_vendidos
# ---------------------------------------------------------------------------

def test_top_sin_ventas_devuelve_lista_vacia():
    gen, _, _ = _generador()
    ranking = gen.top_productos_vendidos()
    assert ranking == []


def test_top_un_producto_aparece_en_ranking():
    gen, repo_v, _ = _generador()
    pid = str(uuid4())
    item = ItemCarrito(producto_id=pid, cantidad=3, precio_unitario=Decimal("2.00"))
    repo_v.guardar(_venta([item], "6.00"))

    ranking = gen.top_productos_vendidos()
    assert len(ranking) == 1
    assert ranking[0].producto_id == pid
    assert ranking[0].cantidad_total == 3
    assert ranking[0].monto_total_usd == Decimal("6.00")


def test_top_acumula_cantidades_de_varias_ventas():
    gen, repo_v, _ = _generador()
    pid = str(uuid4())
    item = ItemCarrito(producto_id=pid, cantidad=2, precio_unitario=Decimal("5.00"))
    repo_v.guardar(_venta([item], "10.00"))
    repo_v.guardar(_venta([item], "10.00"))

    ranking = gen.top_productos_vendidos()
    assert ranking[0].cantidad_total == 4
    assert ranking[0].monto_total_usd == Decimal("20.00")


def test_top_ordena_por_cantidad_descendente():
    gen, repo_v, _ = _generador()
    pid_a, pid_b = str(uuid4()), str(uuid4())
    item_a = ItemCarrito(producto_id=pid_a, cantidad=1, precio_unitario=Decimal("1.00"))
    item_b = ItemCarrito(producto_id=pid_b, cantidad=5, precio_unitario=Decimal("1.00"))
    repo_v.guardar(_venta([item_a, item_b], "6.00"))

    ranking = gen.top_productos_vendidos()
    assert ranking[0].producto_id == pid_b
    assert ranking[1].producto_id == pid_a


def test_top_limite_respetado():
    gen, repo_v, _ = _generador()
    for _ in range(8):
        pid = str(uuid4())
        item = ItemCarrito(producto_id=pid, cantidad=1, precio_unitario=Decimal("1.00"))
        repo_v.guardar(_venta([item], "1.00"))

    assert len(gen.top_productos_vendidos(limite=5)) == 5
    assert len(gen.top_productos_vendidos(limite=3)) == 3


def test_top_filtra_por_rango_de_fechas():
    gen, repo_v, _ = _generador()
    hoy = date.today()
    futuro = date(hoy.year + 1, hoy.month, hoy.day)
    pid = str(uuid4())
    item = ItemCarrito(producto_id=pid, cantidad=10, precio_unitario=Decimal("1.00"))
    # Venta fuera del rango
    repo_v.guardar(_venta([item], "10.00", fecha=futuro))

    ranking = gen.top_productos_vendidos(desde=hoy, hasta=hoy)
    assert ranking == []


def test_top_varios_productos_mismo_periodo():
    gen, repo_v, _ = _generador()
    pid_a, pid_b, pid_c = str(uuid4()), str(uuid4()), str(uuid4())
    items = [
        ItemCarrito(producto_id=pid_a, cantidad=3, precio_unitario=Decimal("2.00")),
        ItemCarrito(producto_id=pid_b, cantidad=7, precio_unitario=Decimal("1.50")),
        ItemCarrito(producto_id=pid_c, cantidad=1, precio_unitario=Decimal("10.00")),
    ]
    repo_v.guardar(_venta(items, "29.50"))

    ranking = gen.top_productos_vendidos(limite=5)
    assert ranking[0].producto_id == pid_b
    assert ranking[0].cantidad_total == 7
    assert ranking[1].producto_id == pid_a
    assert ranking[1].cantidad_total == 3
    assert ranking[2].producto_id == pid_c
