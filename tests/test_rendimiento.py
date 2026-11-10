"""¿Le ganás a la inflación?"""
from datetime import date

import pytest

import rendimiento as r


def punto(f, ars, usd=None, mep=None):
    return {"fecha": f + "T10:00", "patrimonio_ars": ars, "patrimonio_usd": usd, "tipo_cambio_mep": mep}


def test_factor_meses_completos_y_parciales():
    s = [["2026-01", 0.02], ["2026-02", 0.03]]
    assert r.factor_inflacion(s, date(2026, 1, 1), date(2026, 3, 1)) == (pytest.approx(1.02 * 1.03), False)
    # medio enero: la mitad del mes, en forma compuesta
    f, est = r.factor_inflacion(s, date(2026, 1, 1), date(2026, 1, 16))
    assert f == pytest.approx(1.02 ** (15 / 31)) and est is False


def test_meses_sin_publicar_se_estiman():
    s = [["2026-01", 0.02]]
    f, est = r.factor_inflacion(s, date(2026, 1, 1), date(2026, 3, 1))
    assert f == pytest.approx(1.02 ** 2) and est is True
    assert r.factor_inflacion([], date(2026, 1, 1), date(2026, 3, 1)) is None


def test_contra_inflacion():
    s = [["2026-01", 0.02], ["2026-02", 0.02]]
    h = [punto("2026-01-01", 100, 1.0, 100), punto("2026-02-01", 104), punto("2026-03-01", 110, 1.05, 104.8)]
    c = r.contra_inflacion(h, s)
    assert c["var_pesos_pct"] == 10.0 and c["inflacion_pct"] == 4.0
    assert c["real_pct"] == pytest.approx((1.10 / 1.0404 - 1) * 100, abs=0.05)
    assert c["var_usd_pct"] == 5.0 and c["var_mep_pct"] == 4.8 and c["para_empatar"] == 104
    assert [x[0] for x in c["serie"]] == ["2026-01-01", "2026-02-01", "2026-03-01"] and c["serie"][1][2] == 102


def test_perder_contra_la_inflacion():
    c = r.contra_inflacion([punto("2026-01-01", 100), punto("2026-03-01", 101)], [["2026-01", 0.02], ["2026-02", 0.02]])
    assert c["real_pct"] < 0 and "var_usd_pct" not in c


def test_pocos_datos():
    s = [["2026-01", 0.02]]
    assert r.contra_inflacion([], s) is None
    assert r.contra_inflacion([punto("2026-01-01", 100)], None) is None
    assert r.contra_inflacion([punto("2026-01-01", 100), punto("2026-01-04", 101)], s) == {"faltan_dias": 4, "desde": "2026-01-01"}
    assert r.contra_inflacion([punto("2026-01-01", 0), punto("2026-01-20", 101)], s)["faltan_dias"] == 7   # sin patrimonio no cuenta


def test_la_ia_no_recibe_el_grafico():
    import json
    import ia
    p = json.loads(ia.payload({"contra_inflacion": {"real_pct": 3, "serie": [[1, 2, 3]]}, "gastos_por_mes": {}}, {}))
    assert p["contra_inflacion"] == {"real_pct": 3}
