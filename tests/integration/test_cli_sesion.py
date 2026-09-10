"""Escenario 3: sesión de CLI completa con monkeypatch."""

import builtins

import main as main_mod
from config.settings import Settings


def _init_tmp(self, nombre_negocio="Mi Bodega", moneda_base=None, directorio_datos=None, tmp=None):
    self.nombre_negocio = nombre_negocio
    self.moneda_base = moneda_base
    self.directorio_datos = tmp


def test_cli_sesion_completa(capsys, monkeypatch, tmp_path) -> None:
    # Redirige Settings para no tocar data/ real.
    monkeypatch.setattr(
        Settings, "__init__",
        lambda self, nombre_negocio="Mi Bodega", moneda_base=None,
        directorio_datos=None: _init_tmp(
            self, nombre_negocio, moneda_base, directorio_datos, tmp=tmp_path
        ),
    )

    holder = {"id": None}
    real_print = builtins.print

    def fake_print(*args, **kwargs):
        mensaje = " ".join(str(a) for a in args)
        if "producto creado (id=" in mensaje:
            holder["id"] = mensaje.split("id=")[1].split(")")[0]
        real_print(*args, **kwargs)

    marcador = object()
    cola = [
        "1", "b",
        "Aceite", "Alimentos", "USD", "4.00", "30", "10", "2", "litro",
        "2", "a",
        marcador, "5", "compra",
        "3",
        marcador, "2", "listo", "efectivo_usd", "USD",
        "6", "",
        "7",
    ]

    def fake_input(prompt=""):
        valor = cola.pop(0)
        if valor is marcador:
            return holder["id"]
        return valor

    monkeypatch.setattr(builtins, "print", fake_print)
    monkeypatch.setattr(builtins, "input", fake_input)

    main_mod.main()

    out = capsys.readouterr().out
    assert "Traceback" not in out
    assert "OK: producto creado" in out
    assert "OK: entrada registrada" in out
    assert "TICKET" in out
    assert "Ganancia neta" in out
    assert "Hasta luego." in out