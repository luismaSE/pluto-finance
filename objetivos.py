"""Metas de ahorro: cuánto te falta, cuánto tenés que ahorrar por mes y si llegás.

    [objetivos.viaje]
    nombre = "Viaje"
    monto = 3000
    moneda = "USD"          # ARS o USD
    fecha = "2027-07-01"
    ahorrado = 800          # lo que ya tenés apartado para esta meta (lo cargás vos)

El ahorro mensual sale de tus resúmenes (ingresos menos gastos de los últimos meses completos).
Se reparte entre las metas por orden de fecha: primero la más cercana.
"""
from datetime import date

MESES_PROMEDIO = 3


def ahorro_mensual(gastos_por_mes: dict, hoy: date | None = None) -> dict | None:
    """Promedio de ingresos menos gastos de los últimos meses cerrados con ingresos registrados."""
    hoy = hoy or date.today()
    actual = hoy.strftime("%Y-%m")
    meses = sorted(m for m, g in (gastos_por_mes or {}).items() if m < actual and (g.get("ingresos_ars") or 0) > 0)
    meses = meses[-MESES_PROMEDIO:]
    if not meses:
        return None
    vals = [gastos_por_mes[m]["ingresos_ars"] - (gastos_por_mes[m].get("total_ars") or 0) for m in meses]
    return {"promedio": sum(vals) / len(vals), "meses": meses}


def _meses_hasta(hoy: date, fecha: date) -> float:
    return max(0.0, (fecha - hoy).days / 30.44)


def evaluar(cfg: dict, gastos_por_mes: dict, tipo_cambio: float | None, hoy: date | None = None) -> dict:
    hoy = hoy or date.today()
    ahorro = ahorro_mensual(gastos_por_mes, hoy)
    metas = []
    for mid, m in (cfg or {}).items():
        if not isinstance(m, dict):
            continue
        try:
            monto = float(m.get("monto") or 0)
            fecha = date.fromisoformat(str(m.get("fecha"))[:10])
        except (TypeError, ValueError):
            continue
        if monto <= 0:
            continue
        moneda = "USD" if str(m.get("moneda", "ARS")).upper() == "USD" else "ARS"
        ahorrado = max(0.0, float(m.get("ahorrado") or 0))
        a_pesos = (tipo_cambio or 0) if moneda == "USD" else 1
        faltante = max(0.0, monto - ahorrado)
        meses = _meses_hasta(hoy, fecha)
        metas.append({
            "id": mid, "nombre": m.get("nombre") or mid, "monto": monto, "moneda": moneda, "fecha": fecha.isoformat(),
            "ahorrado": ahorrado, "faltante": faltante, "pct": min(100.0, ahorrado / monto * 100),
            "meses_restantes": round(meses, 1),
            # lo que hay que ahorrar por mes, en la moneda de la meta y en pesos (None si falta el dólar)
            "por_mes": faltante / meses if meses >= 0.5 else None,
            "por_mes_ars": (faltante / meses * a_pesos) if meses >= 0.5 and a_pesos else None,
            "faltante_ars": faltante * a_pesos if a_pesos else None,
        })
    metas.sort(key=lambda x: x["fecha"])

    disponible = ahorro["promedio"] if ahorro else None
    for x in metas:
        if x["faltante"] <= 0:
            x["estado"] = "cumplida"
        elif x["por_mes"] is None:
            x["estado"] = "vencida" if x["fecha"] <= hoy.isoformat() else "ultimo_mes"
        elif disponible is None or x["por_mes_ars"] is None:
            x["estado"] = "sin_datos"
        elif x["por_mes_ars"] <= disponible:
            x["estado"] = "en_camino"
            disponible -= x["por_mes_ars"]
        else:
            x["estado"] = "atrasada"
            x["falta_por_mes_ars"] = x["por_mes_ars"] - max(disponible, 0)
            # a este ritmo, ¿cuándo llegaría?
            if disponible > 0 and x["faltante_ars"]:
                meses_reales = x["faltante_ars"] / disponible
                x["llegarias"] = date.fromordinal(hoy.toordinal() + round(meses_reales * 30.44)).isoformat()
            disponible = 0
    return {"metas": metas, "ahorro_mensual": ahorro}


def avisos(res: dict) -> list:
    out = []
    for x in (res or {}).get("metas", []):
        if x.get("estado") == "atrasada":
            out.append({"nivel": "media", "titulo": f"Meta \"{x['nombre']}\" atrasada",
                        "detalle": f"Para llegar a tiempo te faltan unos ${x['falta_por_mes_ars']:,.0f} por mes de ahorro.".replace(",", ".")})
        elif x.get("estado") == "vencida":
            out.append({"nivel": "baja", "titulo": f"Meta \"{x['nombre']}\" vencida",
                        "detalle": "Pasó la fecha y todavía falta. Cambiá la fecha o el monto en Configuración → Metas."})
    return out
