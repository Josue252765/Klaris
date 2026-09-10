"""Entidad Producto y su gestor de CRUD, ambos sin I/O (repositorio inyectado)."""

import unicodedata
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Protocol
from uuid import uuid4

from core.moneda import Moneda, RepositorioTasa
from utils.excepciones import (
    MonedaInvalidaError,
    ProductoNoEncontradoError,
    ValorInvalidoError,
)


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
    codigo: str
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
        self._validar_unidad_medida(self.unidad_medida)
        self._validar_codigo(self.codigo)

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

    def _validar_unidad_medida(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ValorInvalidoError("La unidad de medida no puede estar vacía.")
        if len(valor) > 20:
            raise ValorInvalidoError("La unidad de medida no puede superar los 20 caracteres.")

    def _validar_codigo(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ValorInvalidoError("El código no puede estar vacío.")


class RepositorioProductos(Protocol):
    """Contrato de persistencia de productos que consume GestorProductos."""

    def guardar(self, producto: Producto) -> None: ...

    def obtener(self, id: str) -> Producto | None: ...

    def listar(self) -> list[Producto]: ...

    def actualizar(self, producto: Producto) -> None: ...


class GestorProductos:
    """CRUD de productos sobre repositorios inyectados por constructor."""

    def __init__(
        self,
        repositorio: RepositorioProductos,
        repo_tasa: RepositorioTasa | None = None,
    ) -> None:
        self._repositorio = repositorio
        self._repo_tasa = repo_tasa

    def crear(
        self,
        nombre: str,
        categoria: str,
        costo_unitario: Decimal,
        margen_ganancia: Decimal,
        stock_inicial: int,
        stock_minimo: int,
        unidad_medida: str,
        costo_moneda: Moneda = Moneda.USD,
    ) -> Producto:
        """Construye, guarda y devuelve un producto nuevo; lanza ValorInvalidoError."""
        costo_usd = self._convertir_costo_a_usd(costo_unitario, costo_moneda)
        producto = Producto(
            id=str(uuid4()),
            nombre=nombre,
            categoria=categoria,
            costo_unitario=costo_usd,
            margen_ganancia=margen_ganancia,
            stock_actual=stock_inicial,
            stock_minimo=stock_minimo,
            unidad_medida=unidad_medida,
            codigo=self._generar_codigo(categoria),
        )
        self._repositorio.guardar(producto)
        return producto

    def obtener(self, id: str) -> Producto:
        """Devuelve un producto por id; lanza ProductoNoEncontradoError si falta."""
        producto = self._repositorio.obtener(id)
        if producto is None:
            raise ProductoNoEncontradoError(f"No existe un producto con id {id}.")
        return producto

    def obtener_por_codigo(self, codigo: str) -> Producto:
        """Devuelve un producto por código; lanza ProductoNoEncontradoError si falta."""
        codigo_norm = codigo.strip().upper()
        for producto in self._repositorio.listar():
            if producto.codigo == codigo_norm:
                return producto
        raise ProductoNoEncontradoError(
            f"No existe un producto con código {codigo}."
        )

    def actualizar(
        self, id: str, costo_moneda: Moneda = Moneda.USD, **campos: object
    ) -> Producto:
        """Reconstruye el producto aplicando cambios; el id nunca se modifica."""
        if "id" in campos:
            raise ValorInvalidoError("El id de un producto es inmutable.")
        producto = self.obtener(id)
        if "costo_unitario" in campos and costo_moneda == Moneda.BS:
            campos["costo_unitario"] = self._convertir_costo_a_usd(
                Decimal(campos["costo_unitario"]), costo_moneda
            )
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

    def _convertir_costo_a_usd(
        self, costo: Decimal, moneda: Moneda
    ) -> Decimal:
        """Convierte el costo a USD si viene en BS, usando tasa_referencial."""
        if moneda == Moneda.USD:
            return costo
        if self._repo_tasa is None:
            raise MonedaInvalidaError(
                "No hay repositorio de tasa configurado para convertir BS."
            )
        tasa = self._repo_tasa.obtener_actual()
        if tasa is None:
            raise MonedaInvalidaError(
                "No hay tasa referencial guardada para convertir BS a USD."
            )
        return tasa.convertir(costo, Moneda.BS, Moneda.USD, "referencial")

    def _generar_codigo(self, categoria: str) -> str:
        """Genera un código único PREFIJO-NNNN a partir de la categoría."""
        prefijo = self._prefijo_categoria(categoria)
        return f"{prefijo}-{self._siguiente_secuencia(prefijo)}"

    def _prefijo_categoria(self, categoria: str) -> str:
        """Devuelve las primeras 3 letras de la categoría en mayúsculas, sin acentos ni espacios."""
        normalizada = unicodedata.normalize("NFKD", categoria)
        sin_diacriticos = "".join(
            c for c in normalizada if not unicodedata.combining(c)
        )
        alfanumerico = "".join(c for c in sin_diacriticos if c.isalnum())
        return alfanumerico[:3].upper()

    def _siguiente_secuencia(self, prefijo: str) -> str:
        """Devuelve el número secuencial siguiente para un prefijo, zero-padded a 4 dígitos."""
        numeros = []
        for producto in self._repositorio.listar():
            if producto.codigo.startswith(f"{prefijo}-"):
                sufijo = producto.codigo.split("-", 1)[1]
                if sufijo.isdigit():
                    numeros.append(int(sufijo))
        siguiente = max(numeros) + 1 if numeros else 1
        return f"{siguiente:04d}"