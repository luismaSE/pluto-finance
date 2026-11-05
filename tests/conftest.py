import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


@pytest.fixture
def llavero(monkeypatch):
    """Llavero en memoria: las pruebas nunca tocan el llavero real del sistema."""
    import keyring
    from keyring.backend import KeyringBackend

    class Memoria(KeyringBackend):
        priority = 1

        def __init__(self):
            super().__init__()
            self.d = {}

        def get_password(self, s, n):
            return self.d.get((s, n))

        def set_password(self, s, n, v):
            self.d[(s, n)] = v

        def delete_password(self, s, n):
            self.d.pop((s, n), None)

    m = Memoria()
    anterior = keyring.get_keyring()
    keyring.set_keyring(m)
    yield m
    keyring.set_keyring(anterior)


@pytest.fixture
def carpeta(tmp_path, monkeypatch):
    """Cada prueba corre en una carpeta vacía (config.toml, salida/, etc. no se mezclan)."""
    monkeypatch.chdir(tmp_path)
    return tmp_path
