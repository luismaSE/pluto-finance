"""Análisis de mercado: indicadores, registro de recomendaciones y garantías de solo lectura."""
import tomllib
from datetime import date, timedelta

import pytest

import configuracion
import mercado


def _serie(dias=400, inicio=100.0, paso=0.001, fin=None):
    fin = fin or date(2026, 11, 6)
    out, p = [], inicio
    for d in range(dias, -1, -1):
        out.append([(fin - timedelta(days=d)).isoformat(), round(p, 4)])
        p *= 1 + paso
    return out


def test_indicadores_rendimientos_y_caida():
    s = _serie()
    ind = mercado.indicadores(s)
    assert ind["ultimo"] == s[-1][1]
    assert ind["rend_1m"] == pytest.approx((1.001 ** 30 - 1) * 100, abs=0.1)
    assert ind["rend_12m"] == pytest.approx((1.001 ** 365 - 1) * 100, abs=0.2)
    assert ind["caida_maxima"] == 0 and ind["vs_maximo"] == 0
    # una caída del 20% y recuperación parcial
    s2 = s[:-10] + [[f, s[-11][1] * 0.8] for f, _ in s[-10:-1]] + [[s[-1][0], s[-11][1] * 0.9]]
    ind2 = mercado.indicadores(s2)
    assert ind2["caida_maxima"] == pytest.approx(-20, abs=0.1)
    assert ind2["vs_maximo"] == pytest.approx(-10, abs=0.1)


def test_indicadores_sin_historia_suficiente():
    assert mercado.indicadores(None) == {}
    assert mercado.indicadores(_serie(dias=2)) == {}
    ind = mercado.indicadores(_serie(dias=60))
    assert "rend_1m" in ind and "rend_12m" not in ind      # no inventa rendimientos sin datos


def test_registrar_y_evaluar(carpeta, llavero):
    precios = {"GGAL": {"precio": 100}, "SPY": {"precio": 50}, "MELI": {"precio": 10}}
    analisis = {"recomendaciones": [
        {"accion": "comprar", "activo": "spy", "confianza": "alta"},
        {"accion": "reducir", "activo": "GGAL", "confianza": "media"},
        {"accion": "cambiar", "activo": "MELI", "por": "SPY"},
        {"accion": "mantener", "activo": "Liquidez"},
    ]}
    hace = (date.today() - timedelta(days=10)).isoformat() + "T10:00"
    reg = mercado.registrar(analisis, precios, fecha=hace)
    assert [r["activo"] for r in reg] == ["SPY", "GGAL", "MELI", "LIQUIDEZ"]
    assert reg[0]["precio"] == 50 and reg[2]["precio_por"] == 50 and reg[3]["precio"] is None
    assert mercado.REGISTRO.exists() and b"GGAL" not in mercado.REGISTRO.read_bytes()   # cifrado en disco

    ahora = {"GGAL": {"precio": 90}, "SPY": {"precio": 55}, "MELI": {"precio": 12}}
    ev = {e["activo"]: e for e in mercado.evaluar(reg, ahora)}
    assert ev["SPY"]["acierto"] is True            # compró y subió
    assert ev["GGAL"]["acierto"] is True           # redujo y bajó
    assert ev["MELI"]["acierto"] is False          # MELI +20% le ganó a SPY +10%
    assert ev["LIQUIDEZ"]["acierto"] is None
    assert mercado.resumen_aciertos(list(ev.values())) == {"medibles": 3, "aciertos": 2, "total": 4}
    # recomendaciones recientes no se miden todavía
    assert all(e["acierto"] is None for e in mercado.evaluar(reg, ahora, hoy=date.today() - timedelta(days=5)))


def test_contexto_no_manda_numeros_largos(monkeypatch):
    enviado = {}

    def falso(sistema, contenido, cfg, clave_de, log, web, que):
        enviado.update(contenido=contenido, web=web, sistema=sistema)
        return {"texto": '{"resumen": "ok", "recomendaciones": []}', "proveedor": "X", "modelo": "m", "web": False}

    import ia
    monkeypatch.setattr(ia, "consultar", falso)
    resumen = {"patrimonio_ars": 1000, "inversiones": [{"activo": "GGAL", "ars": 500}],
               "liquidez": [{"entidad": "Banco", "tipo": "CA 1234567890123", "moneda": "ARS", "ars": 500}]}
    a = mercado.analizar(resumen, {}, {"noticias": True}, {"proveedor": "x"}, {}, {}, log=lambda *_: None)
    assert a["resumen"] == "ok" and a["con_noticias"] is False
    assert "1234567890123" not in enviado["contenido"] and enviado["web"] is True
    assert "nunca" in enviado["sistema"].lower() and "ejecutar" in enviado["sistema"]


def test_iol_sesion_solo_lectura():
    from conectores.brokers.iol import SoloLectura
    s = SoloLectura()
    for metodo in ("post", "put", "patch", "delete"):
        with pytest.raises(PermissionError):
            getattr(s, metodo)("https://api.invertironline.com/api/v2/operar/Comprar")


def test_iol_acepta_pedido_de_mercado():
    import inspect
    import pipeline
    from conectores.brokers import BROKERS
    assert pipeline._acepta_extra(BROKERS["iol"])
    assert "extra" in inspect.signature(BROKERS["iol"].obtener).parameters


def test_config_guarda_listas(carpeta):
    cfg = configuracion.cargar()
    assert cfg["mercado"]["activado"] is False and cfg["mercado"]["seguimiento"] == []
    cfg["mercado"]["seguimiento"] = ["SPY", "AAPL:nyse", 'raro"']
    configuracion.guardar(cfg)
    assert tomllib.load(open("config.toml", "rb"))["mercado"]["seguimiento"] == ["SPY", "AAPL:nyse", 'raro"']
    assert configuracion.cargar() == cfg


def test_web_solo_si_el_proveedor_puede(monkeypatch):
    import ia
    llamadas = []

    class Prov:
        ID, NOMBRE, SECRETO, MODELO, WEB = "p", "P", None, "m", False

        @staticmethod
        def disponible(o):
            return True, "ok"

        @staticmethod
        def generar(sistema, contenido, opciones, clave, web=False):
            llamadas.append(web)
            return "{}"

    monkeypatch.setitem(ia.PROVEEDORES, "p", Prov)
    r = ia.consultar("s", "c", {"proveedor": "p"}, web=True, log=lambda *_: None)
    assert r["web"] is False and llamadas == [False]
    Prov.WEB = True
    r = ia.consultar("s", "c", {"proveedor": "p"}, web=True, log=lambda *_: None)
    assert r["web"] is True and llamadas[-1] is True


def test_demo_incluye_mercado(carpeta):
    import pipeline
    r = pipeline.ejecutar(pipeline.Opciones(demo=True, analisis=False), log=lambda *_: None)
    m = r["datos"]["mercado"]
    assert m["analisis"]["recomendaciones"] and m["precios"]["GGAL"]["serie"]
    assert m["aciertos"]["total"] == 4
