"""Clientes y cuentas por cobrar: fiados, saldos y abonos."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import uuid4

from core.moneda import Moneda, RepositorioTasa
from core.ventas import GestorVentas, METODOS_PAGO_VALIDOS
from utils.excepciones import MonedaInvalidaError, ValorInvalidoError
from utils.validadores import validar_monto_positivo, validar_texto_no_vacio

METODOS_ABONO_VALIDOS = METODOS_PAGO_VALIDOS - {"credito"}


@dataclass(frozen=True)
class Cliente:
    """Persona o negocio al que se le fía mercancía."""

    id: str
    nombre: str
    cedula_rif: str
    telefono: str


@dataclass(frozen=True)
class Abono:
    """Pago aplicado a la deuda de un cliente."""

    id: str
    cliente_id: str
    monto_usd: Decimal
    monto_bs: Decimal | None
    tasa_usada: Decimal | None
    metodo_pago: str
    fecha: datetime = field(default_factory=datetime.now)
    nota: str | None = None


class RepositorioClientes(Protocol):
    """Contrato de persistencia de clientes."""

    def guardar(self, cliente: Cliente) -> None: ...

    def obtener(self, id: str) -> Cliente | None: ...

    def listar(self) -> list[Cliente]: ...


class RepositorioAbonos(Protocol):
    """Contrato de persistencia de abonos."""

    def guardar(self, abono: Abono) -> None: ...

    def listar(self) -> list[Abono]: ...


class GestorClientes:
    """Alta de clientes, consulta de deuda y registro de abonos."""

    def __init__(
        self,
        clientes: RepositorioClientes,
        abonos: RepositorioAbonos,
        gestor_ventas: GestorVentas,
        repo_tasa: RepositorioTasa | None = None,
    ) -> None:
        self._clientes = clientes
        self._abonos = abonos
        self._ventas = gestor_ventas
        self._repo_tasa = repo_tasa

    def crear_cliente(self, nombre: str, cedula_rif: str, telefono: str) -> Cliente:
        """Crea y persiste un cliente; lanza si falta un dato o la cédula ya existe."""
        nombre_ok = validar_texto_no_vacio(nombre, "nombre")
        cedula_ok = validar_texto_no_vacio(cedula_rif, "cédula o RIF")
        telefono_ok = validar_texto_no_vacio(telefono, "teléfono")
        self._validar_cedula_unica(cedula_ok)
        cliente = Cliente(
            id=str(uuid4()),
            nombre=nombre_ok,
            cedula_rif=cedula_ok,
            telefono=telefono_ok,
        )
        self._clientes.guardar(cliente)
        return cliente

    def listar_clientes(self) -> list[Cliente]:
        """Devuelve todos los clientes registrados."""
        return self._clientes.listar()

    def obtener(self, cliente_id: str) -> Cliente | None:
        """Devuelve el cliente con ese id o None si no existe."""
        return self._clientes.obtener(cliente_id)

    def obtener_saldo_deuda(self, cliente_id: str) -> Decimal:
        """Saldo en USD: ventas a crédito no anuladas menos abonos; lanza si no hay cliente."""
        self._exigir_cliente(cliente_id)
        credito = self._total_credito_usd(cliente_id)
        abonado = self._total_abonos_usd(cliente_id)
        return credito - abonado

    def registrar_abono(
        self,
        cliente_id: str,
        monto: Decimal,
        moneda_pago: Moneda,
        metodo_pago: str,
        nota: str | None = None,
    ) -> Abono:
        """Registra un abono en USD; convierte BS con tasa diaria. Lanza si el monto excede el saldo."""
        self._exigir_cliente(cliente_id)
        validar_monto_positivo(monto, "monto del abono")
        self._validar_moneda(moneda_pago)
        self._validar_metodo_abono(metodo_pago)
        monto_usd, monto_bs, tasa = self._normalizar_abono(monto, moneda_pago)
        self._validar_contra_saldo(cliente_id, monto_usd)
        abono = Abono(
            id=str(uuid4()),
            cliente_id=cliente_id,
            monto_usd=monto_usd,
            monto_bs=monto_bs,
            tasa_usada=tasa,
            metodo_pago=metodo_pago,
            nota=nota.strip() if isinstance(nota, str) and nota.strip() else None,
        )
        self._abonos.guardar(abono)
        return abono

    def _validar_cedula_unica(self, cedula_rif: str) -> None:
        clave = cedula_rif.casefold()
        for cliente in self._clientes.listar():
            if cliente.cedula_rif.casefold() == clave:
                raise ValorInvalidoError(
                    f"Ya existe un cliente con cédula o RIF {cedula_rif}."
                )

    def _exigir_cliente(self, cliente_id: str) -> Cliente:
        cliente = self._clientes.obtener(cliente_id)
        if cliente is None:
            raise ValorInvalidoError(f"No existe un cliente con id {cliente_id}.")
        return cliente

    def _total_credito_usd(self, cliente_id: str) -> Decimal:
        total = Decimal("0")
        for venta in self._ventas.listar():
            if (
                venta.cliente_id == cliente_id
                and venta.metodo_pago == "credito"
                and not venta.anulada
            ):
                total += venta.total
        return total

    def _total_abonos_usd(self, cliente_id: str) -> Decimal:
        total = Decimal("0")
        for abono in self._abonos.listar():
            if abono.cliente_id == cliente_id:
                total += abono.monto_usd
        return total

    def _validar_moneda(self, moneda: Moneda) -> None:
        if not isinstance(moneda, Moneda):
            raise MonedaInvalidaError("La moneda de pago no es válida.")

    def _validar_metodo_abono(self, metodo_pago: str) -> None:
        if metodo_pago not in METODOS_ABONO_VALIDOS:
            raise ValorInvalidoError(f"Método de pago inválido: {metodo_pago}.")

    def _normalizar_abono(
        self, monto: Decimal, moneda: Moneda
    ) -> tuple[Decimal, Decimal | None, Decimal | None]:
        if moneda == Moneda.USD:
            return monto, None, None
        tasa = self._obtener_tasa_diaria()
        monto_usd = tasa.convertir(monto, Moneda.BS, Moneda.USD, "diaria")
        return monto_usd, monto, tasa.tasa_diaria

    def _obtener_tasa_diaria(self):
        if self._repo_tasa is None:
            raise MonedaInvalidaError(
                "No hay repositorio de tasa configurado para convertir BS."
            )
        tasa = self._repo_tasa.obtener_actual()
        if tasa is None:
            raise MonedaInvalidaError("No hay tasa diaria guardada para convertir BS.")
        return tasa

    def _validar_contra_saldo(self, cliente_id: str, monto_usd: Decimal) -> None:
        saldo = self.obtener_saldo_deuda(cliente_id)
        if saldo <= 0:
            raise ValorInvalidoError("El cliente no tiene deuda pendiente.")
        if monto_usd > saldo:
            raise ValorInvalidoError(
                f"El abono {monto_usd} supera el saldo {saldo}."
            )
