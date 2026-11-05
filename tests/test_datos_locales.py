import json
import os
import time
from pathlib import Path

import datos_locales


def test_cifra_con_llavero(carpeta, llavero):
    datos_locales.escribir(Path("salida/h.json"), [{"patrimonio": 1}])
    assert "patrimonio" not in Path("salida/h.json").read_text()
    assert datos_locales.leer(Path("salida/h.json")) == [{"patrimonio": 1}]
    llavero.d.clear()                                     # otra PC / llavero borrado
    assert datos_locales.leer(Path("salida/h.json"), "x") == "x"


def test_lee_archivos_viejos_sin_cifrar(carpeta, llavero):
    Path("a.json").write_text(json.dumps({"v": 1}))
    assert datos_locales.leer(Path("a.json")) == {"v": 1}


def test_limpiar_dashboards(carpeta):
    Path("salida").mkdir()
    for i in range(6):
        p = Path(f"salida/dashboard_{i}.html"); p.write_text("x"); os.utime(p, (i, i))
    assert datos_locales.limpiar_dashboards("salida", 2) == 4
    assert sorted(p.name for p in Path("salida").glob("*.html")) == ["dashboard_4.html", "dashboard_5.html"]
