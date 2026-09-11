"""Repositorio de TasaCambio sobre JSON."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from core.moneda import TasaCambio
from persistence.json_store import JsonStore


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
