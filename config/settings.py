"""Configuración global del sistema Klaris."""

from pathlib import Path

from core.moneda import Moneda
from utils.excepciones import ValorInvalidoError


class Settings:
    """Configuración central: identidad del negocio, moneda base y rutas de datos."""

    def __init__(
        self,
        nombre_negocio: str = "Mi Bodega",
        moneda_base: Moneda = Moneda.USD,
        directorio_datos: Path = Path("data"),
    ) -> None:
        """Recibe nombre del negocio, moneda base y carpeta de almacenamiento."""
        self._validar_nombre(nombre_negocio)
        self.nombre_negocio = nombre_negocio
        self.moneda_base = moneda_base
        self.directorio_datos = directorio_datos

    def ruta_productos(self) -> Path:
        """Devuelve la ruta del archivo de productos."""
        return self.directorio_datos / "productos.json"

    def ruta_ventas(self) -> Path:
        """Devuelve la ruta del archivo de ventas."""
        return self.directorio_datos / "ventas.json"

    def ruta_gastos(self) -> Path:
        """Devuelve la ruta del archivo de gastos."""
        return self.directorio_datos / "gastos.json"

    def ruta_movimientos(self) -> Path:
        """Devuelve la ruta del archivo de movimientos de stock."""
        return self.directorio_datos / "movimientos_stock.json"

    def ruta_tasas(self) -> Path:
        """Devuelve la ruta del archivo de tasas de cambio."""
        return self.directorio_datos / "tasas.json"

    def _validar_nombre(self, nombre: str) -> None:
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValorInvalidoError("El nombre del negocio no puede estar vacío.")


settings = Settings()
