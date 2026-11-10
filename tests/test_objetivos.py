"""Metas de ahorro."""
from datetime import date

import pytest

import objetivos

HOY = date(2026, 11, 10)
GASTOS = {"2026-08": {"ingresos_ars": 1_000_000, "total_ars": 900_000},     # fuera del promedio (solo 3 meses)
          "2026-09": {"ingresos_ars": 1_000_000, "total_ars": 700_000},
          "2026-10": {"ingresos_ars": 1_000_000, "total_ars": 600_000},
          "2026-07": {"ingresos_ars": 0, "total_ars": 500_000},             # sin ingresos: no cuenta
          "2026-11": {"ingresos_ars": 1_000_000, "total_ars": 100_000}}     # mes en curso: no cuenta


def test_ahorro_mensual_usa_meses_cerrados():
    a = objetivos.ahorro_mensual(GASTOS, HOY)
    assert a["meses"] == ["2026-08", "2026-09", "2026-10"] and a["promedio"] == pytest.approx(266_666.67, abs=1)
    assert objetivos.ahorro_mensual({"2026-11": {"ingresos_ars": 1, "total_ars": 0}}, HOY) is None


def test_reparte_el_ahorro_por_fecha():
    cfg = {
        "lejos": {"nombre": "Auto", "monto": 10_000_000, "fecha": "2027-11-10", "ahorrado": 0},
        "cerca": {"nombre": "Viaje", "monto": 2000, "moneda": "usd", "fecha": "2027-05-10", "ahorrado": 500},
        "lista": {"nombre": "Tele", "monto": 500_000, "fecha": "2027-01-01", "ahorrado": 600_000},
    }
    r = objetivos.evaluar(cfg, GASTOS, 100.0, HOY)
    m = {x["id"]: x for x in r["metas"]}
    assert [x["id"] for x in r["metas"]] == ["lista", "cerca", "lejos"]
    assert m["lista"]["estado"] == "cumplida" and m["lista"]["pct"] == 100
    # Viaje: faltan US$ 1.500 en ~6 meses -> ~US$ 250 por mes -> $ 25.000 a MEP 100
    assert m["cerca"]["moneda"] == "USD" and m["cerca"]["estado"] == "en_camino"
    assert m["cerca"]["por_mes_ars"] == pytest.approx(25_000, rel=0.02)
    # Auto: necesita ~$ 833 k por mes y solo quedan ~$ 242 k
    assert m["lejos"]["estado"] == "atrasada"
    assert m["lejos"]["falta_por_mes_ars"] == pytest.approx(m["lejos"]["por_mes_ars"] - (266_666.67 - m["cerca"]["por_mes_ars"]), rel=0.001)
    assert m["lejos"]["llegarias"] > "2027-11-10"
    assert [a["titulo"] for a in objetivos.avisos(r)] == ['Meta "Auto" atrasada']


def test_casos_borde():
    cfg = {"vieja": {"nombre": "Vieja", "monto": 100, "fecha": "2026-01-01"},
           "ya": {"nombre": "Ya", "monto": 100, "fecha": "2026-11-20"},
           "rota": {"nombre": "Rota", "monto": "mucho", "fecha": "2027-01-01"},
           "sin_fecha": {"nombre": "X", "monto": 100},
           "usd": {"nombre": "Dólares", "monto": 100, "moneda": "USD", "fecha": "2027-11-10"}}
    r = objetivos.evaluar(cfg, GASTOS, None, HOY)
    m = {x["id"]: x for x in r["metas"]}
    assert set(m) == {"vieja", "ya", "usd"}
    assert m["vieja"]["estado"] == "vencida" and m["ya"]["estado"] == "ultimo_mes"
    assert m["usd"]["estado"] == "sin_datos" and m["usd"]["por_mes_ars"] is None   # sin dólar no se puede pasar a pesos
    assert objetivos.evaluar({}, GASTOS, 100, HOY) == {"metas": [], "ahorro_mensual": objetivos.ahorro_mensual(GASTOS, HOY)}
    assert objetivos.avisos(r)[0]["titulo"] == 'Meta "Vieja" vencida'


def test_config_guarda_metas(carpeta):
    import configuracion
    cfg = configuracion.cargar()
    cfg["objetivos"] = {"viaje": {"nombre": "Viaje a Japón", "monto": 3000.5, "moneda": "USD", "fecha": "2027-07-01", "ahorrado": 0}}
    configuracion.guardar(cfg)
    assert configuracion.cargar()["objetivos"] == cfg["objetivos"]
