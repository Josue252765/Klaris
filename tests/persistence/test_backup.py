"""Tests de persistence/backup.py."""

import json
from pathlib import Path
from shutil import copy2

import pytest

import persistence.backup as backup
from persistence.backup import crear_backup
from utils.excepciones import PersistenciaError


def test_crear_backup_copia_todos_los_json(tmp_path) -> None:
    datos = tmp_path / "data"
    backups = tmp_path / "backups"
    datos.mkdir()
    (datos / "productos.json").write_text(
        json.dumps([{"id": "p1"}]), encoding="utf-8"
    )
    (datos / "ventas.json").write_text(
        json.dumps([{"id": "v1"}]), encoding="utf-8"
    )
    (datos / "ignorar.txt").write_text("no copiar", encoding="utf-8")

    destino = crear_backup(datos, backups)

    assert destino.parent == backups
    assert destino.name.startswith("backup_")
    assert sorted(archivo.name for archivo in destino.iterdir()) == [
        "productos.json",
        "ventas.json",
    ]
    assert json.loads((destino / "productos.json").read_text(encoding="utf-8")) == [
        {"id": "p1"}
    ]


def test_crear_backup_limpia_destino_si_falla_una_copia(
    tmp_path, monkeypatch
) -> None:
    datos = tmp_path / "data"
    backups = tmp_path / "backups"
    datos.mkdir()
    (datos / "a.json").write_text("[]", encoding="utf-8")
    (datos / "b.json").write_text("[]", encoding="utf-8")
    llamadas = 0

    def copiar_con_error(origen: Path, destino: Path) -> str:
        nonlocal llamadas
        llamadas += 1
        if llamadas == 2:
            raise OSError("fallo simulado")
        return copy2(origen, destino)

    monkeypatch.setattr(backup, "copy2", copiar_con_error)

    with pytest.raises(PersistenciaError, match="No se pudo crear el backup"):
        crear_backup(datos, backups)

    assert list(backups.iterdir()) == []
