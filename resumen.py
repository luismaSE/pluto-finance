"""Totales consolidados que usan el dashboard y el análisis."""
from collections import defaultdict

from categorias import EXCLUIDAS
from modelo import Snapshot


def _ultimos(items, clave):
    """Si hay varios reportes de la misma cuenta, se queda con el más reciente."""
    best = {}
    for x in items:
        k = clave(x)
        if k not in best or (x.al or "") >= (best[k].al or ""):
            best[k] = x
    return list(best.values())


def calcular(s: Snapshot) -> dict:
    tc = (s.cotizaciones.get("mep") or {}).get("venta")

    def ars(monto, moneda):
        if moneda == "USD":
            return monto * tc if tc else None
        return monto

    def suma(vals):
        return sum(v for v in vals if v is not None)

    cuentas = _ultimos(s.cuentas, lambda c: (c.entidad, c.tipo, c.moneda))
    inversiones = _ultimos(s.inversiones, lambda i: (i.entidad, i.activo, i.moneda))

    liquidez = [{"entidad": c.entidad, "tipo": c.tipo, "moneda": c.moneda, "saldo": c.saldo, "al": c.al,
                 "ars": ars(c.saldo, c.moneda)} for c in cuentas]
    invs = [{**i.__dict__, "ars": ars(i.valuacion, i.moneda)} for i in inversiones]

    tot_liq = suma(x["ars"] for x in liquidez)
    tot_inv = suma(x["ars"] for x in invs)
    total = tot_liq + tot_inv

    por_entidad = defaultdict(float)
    for x in liquidez + invs:
        if x["ars"] is not None:
            por_entidad[x["entidad"]] += x["ars"]
    por_moneda = {"ARS": suma(x["ars"] for x in liquidez + invs if x["moneda"] == "ARS"),
                  "USD": suma(x["ars"] for x in liquidez + invs if x["moneda"] == "USD")}
    por_tipo = defaultdict(float)
    for x in invs:
        if x["ars"] is not None:
            por_tipo[x["tipo"] or "OTROS"] += x["ars"]
    for x in invs:
        x["peso_pct"] = (x["ars"] / tot_inv * 100) if (x["ars"] and tot_inv) else None

    # Gastos e ingresos agrupados por mes (cada reporte puede cubrir un período distinto)
    meses = defaultdict(lambda: {"gastos": [], "ingresos": []})
    vistos = set()
    for m in s.movimientos:
        k = (m.fecha, m.entidad, m.descripcion, round(m.monto, 2))
        if k in vistos or m.categoria in EXCLUIDAS:
            continue
        vistos.add(k)
        meses[m.fecha[:7]]["gastos" if m.monto < 0 else "ingresos"].append(m)

    por_mes = {}
    for mes, d in sorted(meses.items()):
        g_cat, g_ent, i_cat = defaultdict(float), defaultdict(float), defaultdict(float)
        for m in d["gastos"]:
            v = ars(-m.monto, m.moneda) or 0
            g_cat[m.categoria or "Otros"] += v
            g_ent[m.entidad] += v
        for m in d["ingresos"]:
            i_cat[m.categoria or "Otros"] += ars(m.monto, m.moneda) or 0
        top = sorted(d["gastos"], key=lambda m: ars(m.monto, m.moneda) or 0)[:12]
        por_mes[mes] = {
            "total_ars": sum(g_cat.values()),
            "ingresos_ars": sum(i_cat.values()),
            "cantidad": len(d["gastos"]),
            "por_categoria": dict(sorted(g_cat.items(), key=lambda kv: -kv[1])),
            "por_entidad": dict(sorted(g_ent.items(), key=lambda kv: -kv[1])),
            "ingresos_por_categoria": dict(sorted(i_cat.items(), key=lambda kv: -kv[1])),
            "top": [{"fecha": m.fecha, "entidad": m.entidad, "descripcion": m.descripcion,
                     "monto": m.monto, "moneda": m.moneda, "categoria": m.categoria} for m in top],
        }

    return {
        "tipo_cambio_mep": tc,
        "patrimonio_ars": total,
        "patrimonio_usd": total / tc if tc else None,
        "liquidez_ars": tot_liq,
        "inversiones_ars": tot_inv,
        "pesos_liquidos_ars": suma(x["ars"] for x in liquidez if x["moneda"] == "ARS"),
        "por_entidad": dict(sorted(por_entidad.items(), key=lambda kv: -kv[1])),
        "por_moneda": por_moneda,
        "liquidez": liquidez,
        "inversiones": sorted(invs, key=lambda x: -(x["ars"] or 0)),
        "inversiones_por_tipo": dict(sorted(por_tipo.items(), key=lambda kv: -kv[1])),
        "cobertura": s.cobertura,
        "categorias_excluidas": sorted(EXCLUIDAS),
        "gastos_por_mes": por_mes,
    }
