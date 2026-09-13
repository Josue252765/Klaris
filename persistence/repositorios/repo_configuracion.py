"""Repositorio de ConfiguracionNegocio sobre JSON."""

import json
import os
from pathlib import Path

from core.configuracion import ConfiguracionNegocio
from core.moneda import Moneda
from utils.excepciones import PersistenciaError


_ID_REGISTRO = "configuracion_negocio"


def _serializar(config: ConfiguracionNegocio) -> dict:
    return {
        "id": _ID_REGISTRO,
        "nombre_negocio": config.nombre_negocio,
        "mensaje_pie": config.mensaje_pie,
        "moneda_default": config.moneda_default.value,
    }


def _deserializar(r: dict) -> ConfiguracionNegocio:
    try:
        moneda = Moneda(r["moneda_default"])
    except (KeyError, ValueError) as exc:
        raise PersistenciaError(
            "La configuración tiene un valor de moneda inválido."
        ) from exc
    return ConfiguracionNegocio(
        nombre_negocio=r["nombre_negocio"],
        mensaje_pie=r["mensaje_pie"],
        moneda_default=moneda,
    )


class RepositorioConfiguracionJSON:
    """Persistencia de ConfiguracionNegocio en data/configuracion_negocio.json.
    Registro único (no lista).
    """

    def __init__(self, filepath: Path | None = None) -> None:
        self._filepath = filepath or Path("data/configuracion_negocio.json")
        self._filepath.parent.mkdir(parents=True, exist_ok=True)

    def obtener(self) -> ConfiguracionNegocio | None:
        """Devuelve la configuración guardada o None si no existe."""
        if not self._filepath.exists():
            return None
        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                contenido = f.read()
        except OSError as exc:
            raise PersistenciaError(
                f"No se pudo leer {self._filepath}: {exc}"
            ) from exc
        if not contenido.strip():
            return None
        try:
            registros = json.loads(contenido)
        except json.JSONDecodeError as exc:
            raise PersistenciaError(
                f"El archivo de configuración no es JSON válido: {exc}"
            ) from exc
        for r in registros:
            if r.get("id") == _ID_REGISTRO:
                return _deserializar(r)
        return None

    def guardar(self, config: ConfiguracionNegocio) -> None:
        """Sobrescribe el registro único de configuración."""
        serializado = _serializar(config)
        registros = []
        if self._filepath.exists():
            try:
                with open(self._filepath, "r", encoding="utf-8") as f:
                    contenido = f.read()
            except OSError as exc:
                raise PersistenciaError(
                    f"No se pudo leer {self._filepath}: {exc}"
                ) from exc
            if contenido.strip():
                try:
                    registros = json.loads(contenido)
                except json.JSONDecodeError as exc:
                    raise PersistenciaError(
                        f"El archivo de configuración no es JSON válido: {exc}"
                    ) from exc
        for i, existing in enumerate(registros):
            if existing.get("id") == _ID_REGISTRO:
                registros[i] = serializado
                break
        else:
            registros.append(serializado)
        tmp = self._filepath.with_suffix(self._filepath.suffix + ".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(registros, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self._filepath)
        except OSError as exc:
            tmp.unlink(missing_ok=True)
            raise PersistenciaError(
                f"No se pudo escribir {self._filepath}: {exc}"
            ) from exc
