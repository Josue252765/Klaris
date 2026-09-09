"""Almacenamiento JSON genérico en disco, con escritura atómica."""

import json
import os
from pathlib import Path

from utils.excepciones import PersistenciaError


class JsonStore:
    """Lee y escribe una lista de diccionarios en un archivo JSON."""

    def __init__(self, filepath: Path) -> None:
        """Recibe la ruta del archivo; crea el directorio padre si no existe."""
        self._filepath = filepath
        self._filepath.parent.mkdir(parents=True, exist_ok=True)

    def guardar(self, registro: dict) -> None:
        """Añade un registro al final del archivo, de forma atómica."""
        registros = self.listar()
        registros.append(registro)
        self._escribir_atomico(registros)

    def obtener(self, id: str) -> dict | None:
        """Busca un registro por id; devuelve None si no existe."""
        for r in self.listar():
            if r.get("id") == id:
                return r
        return None

    def listar(self) -> list[dict]:
        """Devuelve todos los registros; lista vacía si el archivo no existe."""
        if not self._filepath.exists():
            return []
        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                contenido = f.read()
        except OSError as exc:
            raise PersistenciaError(f"No se pudo leer {self._filepath}: {exc}") from exc
        if not contenido.strip():
            return []
        return json.loads(contenido)

    def actualizar(self, registro: dict) -> None:
        """Reemplaza el registro cuyo id coincide con el del registro dado."""
        registros = self.listar()
        for i, r in enumerate(registros):
            if r.get("id") == registro.get("id"):
                registros[i] = registro
                self._escribir_atomico(registros)
                return
        raise PersistenciaError(
            f"No existe un registro con id {registro.get('id')}."
        )

    def _escribir_atomico(self, registros: list[dict]) -> None:
        """Escribe en un archivo temporal y lo renombra al destino."""
        tmp = self._filepath.with_suffix(self._filepath.suffix + ".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(registros, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self._filepath)
        except OSError as exc:
            tmp.unlink(missing_ok=True)
            raise PersistenciaError(f"No se pudo escribir {self._filepath}: {exc}") from exc