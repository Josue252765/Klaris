"""Repositorios concretos sobre JSON, cumplen los Protocols de core/."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from core.clientes import Abono, Cliente
from core.devoluciones import AnulacionVenta
from core.gastos import CategoriaGasto, Gasto
from core.inventario import MovimientoStock
from core.moneda import Moneda, TasaCambio
from core.producto import Producto
from core.ventas import ItemCarrito, Venta
from persistence.json_store import JsonStore


class RepositorioProductosJSON:
    """Persistencia de Producto en data/productos.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/productos.json"))

    def guardar(self, producto: Producto) -> None:
        """Persiste un producto como diccionario."""
        self._store.guardar(self._serializar(producto))

    def obtener(self, id: str) -> Producto | None:
        """Busca un producto por id; devuelve None si no existe."""
        registro = self._store.obtener(id)
        return self._deserializar(registro) if registro else None

    def listar(self) -> list[Producto]:
        """Devuelve todos los productos."""
        return [self._deserializar(r) for r in self._store.listar()]

    def actualizar(self, producto: Producto) -> None:
        """Reemplaza el producto con el mismo id."""
        self._store.actualizar(self._serializar(producto))

    def _serializar(self, p: Producto) -> dict:
        return {
            "id": p.id,
            "nombre": p.nombre,
            "categoria": p.categoria,
            "costo_unitario": str(p.costo_unitario),
            "margen_ganancia": str(p.margen_ganancia),
            "stock_actual": p.stock_actual,
            "stock_minimo": p.stock_minimo,
            "unidad_medida": p.unidad_medida,
            "codigo": p.codigo,
            "activo": p.activo,
        }

    def _deserializar(self, r: dict) -> Producto:
        return Producto(
            id=r["id"],
            nombre=r["nombre"],
            categoria=r["categoria"],
            costo_unitario=Decimal(r["costo_unitario"]),
            margen_ganancia=Decimal(r["margen_ganancia"]),
            stock_actual=r["stock_actual"],
            stock_minimo=r["stock_minimo"],
            unidad_medida=r["unidad_medida"],
            codigo=r["codigo"],
            activo=r["activo"],
        )


class RepositorioMovimientosJSON:
    """Persistencia de MovimientoStock en data/movimientos_stock.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/movimientos_stock.json"))

    def guardar(self, movimiento: MovimientoStock) -> None:
        """Persiste un movimiento como diccionario."""
        self._store.guardar(self._serializar(movimiento))

    def listar(self) -> list[MovimientoStock]:
        """Devuelve todos los movimientos en orden de registro."""
        return [self._deserializar(r) for r in self._store.listar()]

    def _serializar(self, m: MovimientoStock) -> dict:
        return {
            "producto_id": m.producto_id,
            "tipo": m.tipo,
            "cantidad": m.cantidad,
            "motivo": m.motivo,
            "fecha": m.fecha.isoformat(),
        }

    def _deserializar(self, r: dict) -> MovimientoStock:
        return MovimientoStock(
            producto_id=r["producto_id"],
            tipo=r["tipo"],
            cantidad=r["cantidad"],
            motivo=r["motivo"],
            fecha=datetime.fromisoformat(r["fecha"]),
        )


class RepositorioVentasJSON:
    """Persistencia de Venta en data/ventas.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/ventas.json"))

    def guardar(self, venta: Venta) -> None:
        """Persiste una venta como diccionario."""
        self._store.guardar(self._serializar(venta))

    def listar(self) -> list[Venta]:
        """Devuelve todas las ventas."""
        return [self._deserializar(r) for r in self._store.listar()]

    def _serializar(self, v: Venta) -> dict:
        return {
            "id": v.id,
            "items": [
                {
                    "producto_id": i.producto_id,
                    "cantidad": i.cantidad,
                    "precio_unitario": str(i.precio_unitario),
                }
                for i in v.items
            ],
            "total": str(v.total),
            "moneda": v.moneda.value,
            "metodo_pago": v.metodo_pago,
            "fecha": v.fecha.isoformat(),
            "total_bs": str(v.total_bs) if v.total_bs is not None else None,
            "tasa_usada": str(v.tasa_usada) if v.tasa_usada is not None else None,
            "monto_recibido_bs": str(v.monto_recibido_bs) if v.monto_recibido_bs is not None else None,
            "vuelto_bs": str(v.vuelto_bs) if v.vuelto_bs is not None else None,
            "anulada": v.anulada,
            "cliente_id": v.cliente_id,
        }

    def actualizar(self, venta: Venta) -> None:
        """Reemplaza la venta con el mismo id."""
        self._store.actualizar(self._serializar(venta))

    def _deserializar(self, r: dict) -> Venta:
        items = [
            ItemCarrito(
                producto_id=i["producto_id"],
                cantidad=i["cantidad"],
                precio_unitario=Decimal(i["precio_unitario"]),
            )
            for i in r["items"]
        ]
        return Venta(
            id=r["id"],
            items=items,
            total=Decimal(r["total"]),
            moneda=Moneda(r["moneda"]),
            metodo_pago=r["metodo_pago"],
            fecha=datetime.fromisoformat(r["fecha"]),
            total_bs=Decimal(r["total_bs"]) if r.get("total_bs") is not None else None,
            tasa_usada=Decimal(r["tasa_usada"]) if r.get("tasa_usada") is not None else None,
            monto_recibido_bs=Decimal(r["monto_recibido_bs"]) if r.get("monto_recibido_bs") is not None else None,
            vuelto_bs=Decimal(r["vuelto_bs"]) if r.get("vuelto_bs") is not None else None,
            anulada=bool(r.get("anulada", False)),
            cliente_id=r.get("cliente_id"),
        )


class RepositorioGastosJSON:
    """Persistencia de Gasto en data/gastos.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/gastos.json"))

    def guardar(self, gasto: Gasto) -> None:
        """Persiste un gasto como diccionario."""
        self._store.guardar(self._serializar(gasto))

    def listar(self) -> list[Gasto]:
        """Devuelve todos los gastos."""
        return [self._deserializar(r) for r in self._store.listar()]

    def _serializar(self, g: Gasto) -> dict:
        return {
            "id": g.id,
            "categoria": g.categoria.value,
            "descripcion": g.descripcion,
            "monto": str(g.monto),
            "moneda": g.moneda.value,
            "fecha": g.fecha.isoformat(),
            "monto_original": str(g.monto_original) if g.monto_original is not None else None,
            "moneda_original": g.moneda_original.value if g.moneda_original is not None else None,
            "tasa_usada": str(g.tasa_usada) if g.tasa_usada is not None else None,
        }

    def _deserializar(self, r: dict) -> Gasto:
        return Gasto(
            id=r["id"],
            categoria=CategoriaGasto(r["categoria"]),
            descripcion=r["descripcion"],
            monto=Decimal(r["monto"]),
            moneda=Moneda(r["moneda"]),
            fecha=datetime.fromisoformat(r["fecha"]),
            monto_original=Decimal(r["monto_original"]) if r.get("monto_original") is not None else None,
            moneda_original=Moneda(r["moneda_original"]) if r.get("moneda_original") is not None else None,
            tasa_usada=Decimal(r["tasa_usada"]) if r.get("tasa_usada") is not None else None,
        )


class RepositorioTasaJSON:
    """Persistencia de TasaCambio en data/tasas.json. Registro único (no historial)."""

    _ID_REGISTRO = "tasa_actual"

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/tasas.json"))

    def obtener_actual(self) -> TasaCambio | None:
        """Devuelve la tasa vigente o None si no hay ninguna guardada."""
        registros = self._store.listar()
        if not registros:
            return None
        return self._deserializar(registros[0])

    def guardar(self, tasa: TasaCambio) -> None:
        """Sobrescribe el único registro de tasa (no agrega, reemplaza)."""
        registros = self._store.listar()
        serializado = self._serializar(tasa)
        if registros:
            self._store.actualizar(serializado)
        else:
            self._store.guardar(serializado)

    def _serializar(self, t: TasaCambio) -> dict:
        return {
            "id": self._ID_REGISTRO,
            "tasa_referencial": str(t.tasa_referencial),
            "tasa_referencial_fecha": t.tasa_referencial_fecha.isoformat(),
            "tasa_diaria": str(t.tasa_diaria),
            "tasa_diaria_fecha": t.tasa_diaria_fecha.isoformat(),
        }

    def _deserializar(self, r: dict) -> TasaCambio:
        return TasaCambio(
            tasa_referencial=Decimal(r["tasa_referencial"]),
            tasa_referencial_fecha=date.fromisoformat(r["tasa_referencial_fecha"]),
            tasa_diaria=Decimal(r["tasa_diaria"]),
            tasa_diaria_fecha=date.fromisoformat(r["tasa_diaria_fecha"]),
        )


class RepositorioAnulacionesJSON:
    """Persistencia de AnulacionVenta en data/anulaciones.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/anulaciones.json"))

    def guardar(self, anulacion: AnulacionVenta) -> None:
        """Persiste una anulación como diccionario."""
        self._store.guardar(self._serializar(anulacion))

    def listar(self) -> list[AnulacionVenta]:
        """Devuelve todas las anulaciones."""
        return [self._deserializar(r) for r in self._store.listar()]

    def _serializar(self, a: AnulacionVenta) -> dict:
        return {
            "id": a.id,
            "venta_id": a.venta_id,
            "motivo": a.motivo,
            "fecha": a.fecha.isoformat(),
            "monto_devuelto_usd": str(a.monto_devuelto_usd),
        }

    def _deserializar(self, r: dict) -> AnulacionVenta:
        return AnulacionVenta(
            id=r["id"],
            venta_id=r["venta_id"],
            motivo=r["motivo"],
            fecha=datetime.fromisoformat(r["fecha"]),
            monto_devuelto_usd=Decimal(r["monto_devuelto_usd"]),
        )


class RepositorioClientesJSON:
    """Persistencia de Cliente en data/clientes.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/clientes.json"))

    def guardar(self, cliente: Cliente) -> None:
        """Persiste un cliente como diccionario."""
        self._store.guardar(self._serializar(cliente))

    def obtener(self, id: str) -> Cliente | None:
        """Busca un cliente por id; devuelve None si no existe."""
        registro = self._store.obtener(id)
        return self._deserializar(registro) if registro else None

    def listar(self) -> list[Cliente]:
        """Devuelve todos los clientes."""
        return [self._deserializar(r) for r in self._store.listar()]

    def _serializar(self, c: Cliente) -> dict:
        return {
            "id": c.id,
            "nombre": c.nombre,
            "cedula_rif": c.cedula_rif,
            "telefono": c.telefono,
        }

    def _deserializar(self, r: dict) -> Cliente:
        return Cliente(
            id=r["id"],
            nombre=r["nombre"],
            cedula_rif=r["cedula_rif"],
            telefono=r["telefono"],
        )


class RepositorioAbonosJSON:
    """Persistencia de Abono en data/abonos.json."""

    def __init__(self, filepath: Path | None = None) -> None:
        self._store = JsonStore(filepath or Path("data/abonos.json"))

    def guardar(self, abono: Abono) -> None:
        """Persiste un abono como diccionario."""
        self._store.guardar(self._serializar(abono))

    def listar(self) -> list[Abono]:
        """Devuelve todos los abonos."""
        return [self._deserializar(r) for r in self._store.listar()]

    def _serializar(self, a: Abono) -> dict:
        return {
            "id": a.id,
            "cliente_id": a.cliente_id,
            "monto_usd": str(a.monto_usd),
            "monto_bs": str(a.monto_bs) if a.monto_bs is not None else None,
            "tasa_usada": str(a.tasa_usada) if a.tasa_usada is not None else None,
            "metodo_pago": a.metodo_pago,
            "fecha": a.fecha.isoformat(),
            "nota": a.nota,
        }

    def _deserializar(self, r: dict) -> Abono:
        return Abono(
            id=r["id"],
            cliente_id=r["cliente_id"],
            monto_usd=Decimal(r["monto_usd"]),
            monto_bs=Decimal(r["monto_bs"]) if r.get("monto_bs") is not None else None,
            tasa_usada=Decimal(r["tasa_usada"]) if r.get("tasa_usada") is not None else None,
            metodo_pago=r["metodo_pago"],
            fecha=datetime.fromisoformat(r["fecha"]),
            nota=r.get("nota"),
        )