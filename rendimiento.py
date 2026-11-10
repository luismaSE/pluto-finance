"""¿Le ganás a la inflación? Compara cómo cambió tu patrimonio con la inflación y con el dólar MEP.

Ojo: el patrimonio sube también por lo que ahorrás (y baja por lo que gastás), no solo por lo que
rinden tus inversiones. Por eso se presenta como "tu patrimonio contra la inflación", no como
rendimiento de la cartera.
"""
import calendar
from datetime import date

MIN_DIAS = 7


def _tasas_por_mes(serie: list) -> dict:
    """[["2026-09", 0.021], ...] (tasa mensual en fracción) -> {"2026-09": 0.021}."""
    out = {}
    for f, v in serie or []:
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        out[str(f)[:7]] = v
    return out


def factor_inflacion(serie: list, desde: date, hasta: date) -> tuple[float, bool] | None:
    """Cuánto subieron los precios entre dos fechas (1.10 = 10%). Reparte cada mes en sus días.
    Los meses sin dato publicado usan el último conocido y se marcan como estimados."""
    tasas = _tasas_por_mes(serie)
    if not tasas or hasta <= desde:
        return (1.0, False) if tasas else None
    ultima = tasas[max(tasas)]
    factor, estimado = 1.0, False
    d = desde
    while d < hasta:
        mes = d.strftime("%Y-%m")
        dias_mes = calendar.monthrange(d.year, d.month)[1]
        fin_mes = date(d.year, d.month, dias_mes)
        tramo = (min(hasta, date.fromordinal(fin_mes.toordinal() + 1)) - d).days
        if mes in tasas:
            r = tasas[mes]
        else:
            anteriores = [m for m in tasas if m < mes]
            r = tasas[max(anteriores)] if anteriores else ultima
            estimado = True
        factor *= (1 + r) ** (tramo / dias_mes)
        d = date.fromordinal(d.toordinal() + tramo)
    return factor, estimado


def contra_inflacion(historial_por_dia: list, serie_inflacion: list) -> dict | None:
    """Resultado para el dashboard y la IA, o None si no hay datos suficientes."""
    puntos = [x for x in historial_por_dia or [] if (x.get("patrimonio_ars") or 0) > 0]
    if not puntos or not serie_inflacion:
        return None
    a, b = puntos[0], puntos[-1]
    d0, d1 = date.fromisoformat(a["fecha"][:10]), date.fromisoformat(b["fecha"][:10])
    dias = (d1 - d0).days
    if dias < MIN_DIAS:
        return {"faltan_dias": MIN_DIAS - dias, "desde": d0.isoformat()}
    f = factor_inflacion(serie_inflacion, d0, d1)
    if not f:
        return None
    factor, estimado = f
    p0, p1 = a["patrimonio_ars"], b["patrimonio_ars"]
    var_pesos = p1 / p0 - 1
    out = {
        "desde": d0.isoformat(), "hasta": d1.isoformat(), "dias": dias, "estimado": estimado,
        "patrimonio_inicial": p0, "patrimonio_final": p1,
        "var_pesos_pct": round(var_pesos * 100, 1),
        "inflacion_pct": round((factor - 1) * 100, 1),
        "real_pct": round(((1 + var_pesos) / factor - 1) * 100, 1),
        "para_empatar": round(p0 * factor),
        "serie": [],
    }
    u0, u1 = a.get("patrimonio_usd"), b.get("patrimonio_usd")
    if u0 and u1:
        out["var_usd_pct"] = round((u1 / u0 - 1) * 100, 1)
    m0, m1 = a.get("tipo_cambio_mep"), b.get("tipo_cambio_mep")
    if m0 and m1:
        out["var_mep_pct"] = round((m1 / m0 - 1) * 100, 1)
    for x in puntos:
        fx = factor_inflacion(serie_inflacion, d0, date.fromisoformat(x["fecha"][:10]))
        out["serie"].append([x["fecha"][:10], x["patrimonio_ars"], round(p0 * fx[0]) if fx else None])
    return out
