"""Creación de copias de respaldo de los archivos JSON del negocio."""

from datetime import datetime
from pathlib import Path
from shutil import copy2, rmtree

from utils.excepciones import PersistenciaError


def crear_backup(directorio_datos: Path, directorio_backups: Path) -> Path:
    """Copia los JSON de datos a una carpeta fechada y devuelve su ruta."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    destino = directorio_backups / f"backup_{timestamp}"
    temporal = directorio_backups / f".{destino.name}.tmp"
    try:
        temporal.mkdir(parents=True, exist_ok=False)
        for archivo in sorted(directorio_datos.glob("*.json")):
            copy2(archivo, temporal / archivo.name)
        temporal.rename(destino)
    except OSError as exc:
        if temporal.exists():
            rmtree(temporal, ignore_errors=True)
        raise PersistenciaError(f"No se pudo crear el backup: {exc}") from exc
    return destino
