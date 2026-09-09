"""Entidad Producto y su gestor de CRUD, ambos sin I/O (repositorio inyectado)."""

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Protocol
from uuid import uuid4

from utils.excepciones import ProductoNoEncontradoError, ValorInvalidoError


@dataclass(frozen=True)
class Producto:
    """Producto del negocio. Inmutable: todo cambio se expresa reconstruyéndolo."""

    id: str
    nombre: str
    categoria: str
    costo_unitario: Decimal
    margen_ganancia: Decimal
    stock_actual: int
    stock_minimo: int
    unidad_medida: str
    activo: bool = True

    def __post_init__(self) -> None:
        """Valida todos los campos en construcción; lanza ValorInvalidoError."""
        self._validar_id(self.id)
        self._validar_nombre(self.nombre)
        self._validar_categoria(self.categoria)
        self._validar_decimal_no_negativo(self.costo_unitario, "costo_unitario")
        self._validar_decimal(self.margen_ganancia, "margen_ganancia")
        self._validar_entero_no_negativo(self.stock_actual, "stock_actual")
        self._validar_entero_no_negativo(self.stock_minimo, "stock_minimo")
        self._validar_nombre(self.unidad_medida)

    def _validar_id(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor:
            raise ValorInvalidoError("El id debe ser un texto no vacío.")

    def _validar_nombre(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ValorInvalidoError("El nombre no puede estar vacío.")
        if len(valor) > 100:
            raise ValorInvalidoError("El nombre no puede superar los 100 caracteres.")

    def _validar_categoria(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ValorInvalidoError("La categoría no puede estar vacía.")

    def _validar_decimal(self, valor: Decimal, campo: str) -> None:
        if not isinstance(valor, Decimal):
            raise ValorInvalidoError(f"{campo} debe ser Decimal, nunca float.")

    def _validar_decimal_no_negativo(self, valor: Decimal, campo: str) -> None:
        self._validar_decimal(valor, campo)
        if valor < 0:
            raise ValorInvalidoError(f"{campo} no puede ser negativo.")

    def _validar_entero_no_negativo(self, valor: int, campo: str) -> None:
        if not isinstance(valor, int) or isinstance(valor, bool):
            raise ValorInvalidoError(f"{campo} debe ser un entero.")
        if valor < 0:
            raise ValorInvalidoError(f"{campo} no puede ser negativo.")


class RepositorioProductos(Protocol):
    """Contrato de persistencia de productos que consume GestorProductos."""

    def guardar(self, producto: Producto) -> None: ...

    def obtener(self, id: str) -> Producto | None: ...

    def listar(self) -> list[Producto]: ...

    def actualizar(self, producto: Producto) -> None: ...


class GestorProductos:
    """CRUD de productos sobre un repositorio inyectado por constructor."""

    def __init__(self, repositorio: RepositorioProductos) -> None:
        self._repositorio = repositorio

    def crear(
        self,
        nombre: str,
        categoria: str,
        costo_unitario: Decimal,
        margen_ganancia: Decimal,
        stock_inicial: int,
        stock_minimo: int,
        unidad_medida: str,
    ) -> Producto:
        """Construye, guarda y devuelve un producto nuevo; lanza ValorInvalidoError."""
        producto = Producto(
            id=str(uuid4()),
            nombre=nombre,
            categoria=categoria,
            costo_unitario=costo_unitario,
            margen_ganancia=margen_ganancia,
            stock_actual=stock_inicial,
            stock_minimo=stock_minimo,
            unidad_medida=unidad_medida,
        )
        self._repositorio.guardar(producto)
        return producto

    def obtener(self, id: str) -> Producto:
        """Devuelve un producto por id; lanza ProductoNoEncontradoError si falta."""
        producto = self._repositorio.obtener(id)
        if producto is None:
            raise ProductoNoEncontradoError(f"No existe un producto con id {id}.")
        return producto

    def actualizar(self, id: str, **campos: object) -> Producto:
        """Reconstruye el producto aplicando cambios; el id nunca se modifica."""
        producto = self.obtener(id)
        actualizado = replace(producto, **campos)
        self._repositorio.actualizar(actualizado)
        return actualizado

    def desactivar(self, id: str) -> None:
        """Marca un producto como inactivo (soft delete); lanza si no existe."""
        producto = self.obtener(id)
        if producto.activo:
            self._repositorio.actualizar(replace(producto, activo=False))

    def listar(self, solo_activos: bool = True) -> list[Producto]:
        """Lista productos, filtrando inactivos por defecto."""
        productos = self._repositorio.listar()
        if solo_activos:
            return [p for p in productos if p.activo]
        return productos

    def buscar_por_nombre(self, texto: str) -> list[Producto]:
        """Busca productos cuyo nombre contenga el texto, sin distinguir mayúsculas."""
        patron = texto.strip().lower()
        return [
            p for p in self._repositorio.listar() if patron in p.nombre.lower()
        ]