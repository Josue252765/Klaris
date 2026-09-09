"""Tests de persistence/json_store.py: lectura, escritura y atomicidad."""

import json

import pytest

from persistence.json_store import JsonStore
from utils.excepciones import PersistenciaError


def test_leer_todos_archivo_inexistente_devuelve_vacio(tmp_path) -> None:
    store = JsonStore(tmp_path / "no_existe.json")
    assert store.leer_todos() == []


def test_guardar_y_leer_roundtrip(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    store.guardar_todos([{"id": "1", "valor": "a"}, {"id": "2", "valor": "b"}])
    assert store.leer_todos() == [{"id": "1", "valor": "a"}, {"id": "2", "valor": "b"}]


def test_agregar_añade_al_final(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    store.agregar({"id": "1", "v": 10})
    store.agregar({"id": "2", "v": 20})
    registros = store.leer_todos()
    assert len(registros) == 2
    assert registros[1]["v"] == 20


def test_actualizar_cambia_registro_existente(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    store.agregar({"id": "1", "v": 10})
    store.actualizar("1", {"v": 99})
    assert store.leer_todos()[0]["v"] == 99


def test_actualizar_inexistente_lanza(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    with pytest.raises(PersistenciaError):
        store.actualizar("x", {"v": 1})


def test_eliminar_borra_registro(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    store.agregar({"id": "1", "v": 10})
    store.agregar({"id": "2", "v": 20})
    store.eliminar("1")
    registros = store.leer_todos()
    assert len(registros) == 1
    assert registros[0]["id"] == "2"


def test_eliminar_inexistente_lanza(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    store.agregar({"id": "1", "v": 10})
    with pytest.raises(PersistenciaError):
        store.eliminar("x")


def test_crea_directorio_padre_si_no_existe(tmp_path) -> None:
    store = JsonStore(tmp_path / "sub" / "otro" / "datos.json")
    store.guardar_todos([{"id": "1"}])
    assert (tmp_path / "sub" / "otro" / "datos.json").exists()


def test_escritura_atomica_no_deja_tmp(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    store.guardar_todos([{"id": "1", "v": 1}])
    assert not (tmp_path / "datos.json.tmp").exists()


def test_escritura_atomica_contenido_valido(tmp_path) -> None:
    store = JsonStore(tmp_path / "datos.json")
    store.guardar_todos([{"id": "1", "v": 42}])
    with open(tmp_path / "datos.json", "r", encoding="utf-8") as f:
        assert json.load(f) == [{"id": "1", "v": 42}]


def test_leer_archivo_vacio_devuelve_lista_vacia(tmp_path) -> None:
    filepath = tmp_path / "vacio.json"
    filepath.write_text("", encoding="utf-8")
    store = JsonStore(filepath)
    assert store.leer_todos() == []