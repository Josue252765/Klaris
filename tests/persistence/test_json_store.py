"""Tests de persistence/json_store.py: lectura, escritura y atomicidad."""

import json

import pytest

from persistence.json_store import JsonStore
from utils.excepciones import PersistenciaError


def test_listar_archivo_inexistente_devuelve_vacio(tmp_path) -> None:
    store = JsonStore(tmp_path / "no_existe.json")
    assert store.listar() == []


def test_guardar_y_listar_roundtrip(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    store.guardar({"id": "1", "valor": "a"})
    store.guardar({"id": "2", "valor": "b"})
    assert store.listar() == [{"id": "1", "valor": "a"}, {"id": "2", "valor": "b"}]


def test_obtener_existente(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    store.guardar({"id": "1", "v": 10})
    assert store.obtener("1") == {"id": "1", "v": 10}


def test_obtener_inexistente_devuelve_none(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    store.guardar({"id": "1", "v": 10})
    assert store.obtener("x") is None


def test_actualizar_reemplaza_registro(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    store.guardar({"id": "1", "v": 10})
    store.actualizar({"id": "1", "v": 99})
    assert store.listar()[0]["v"] == 99


def test_actualizar_inexistente_lanza(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    with pytest.raises(PersistenciaError):
        store.actualizar({"id": "x", "v": 1})


def test_crea_directorio_padre_si_no_existe(tmp_path) -> None:
    store = JsonStore(tmp_path / "sub" / "otro" / "datos.json")
    store.guardar({"id": "1"})
    assert (tmp_path / "sub" / "otro" / "datos.json").exists()


def test_escritura_atomica_no_deja_tmp(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    store.guardar({"id": "1", "v": 1})
    assert not (tmp_path / "datos.json.tmp").exists()


def test_escritura_atomica_contenido_valido(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    store.guardar({"id": "1", "v": 42})
    with open(tmp_path / "datos.json", "r", encoding="utf-8") as f:
        assert json.load(f) == [{"id": "1", "v": 42}]


def test_listar_archivo_vacio_devuelve_lista_vacia(tmp_path) -> None:
    filepath = tmp_path / "vacio.json"
    filepath.write_text("", encoding="utf-8")
    store = JsonStore(filepath)
    assert store.listar() == []