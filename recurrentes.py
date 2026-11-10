"""Pagos que se repiten todos los meses (suscripciones, servicios, comisiones) y cuándo suben.

Un pago cuenta como recurrente si aparece una vez por mes durante al menos 2 meses con montos
parecidos, o si su categoría es Suscripciones. Si el último cobro es al menos 5% más caro que el
anterior, se marca como aumento y se avisa.
"""
import re
import statistics
import unicodedata
from collections import defaultdict

AUMENTO_MIN_PCT = 5
AUMENTO_MIN_ARS = 500
NO_RECURRENTES = {"Pago de tarjeta"}


def clave(descripcion: str) -> str:
    t = unicodedata.normalize("NFD", str(descripcion).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"\d{4,}", "", t)              # números de operación, fechas pegadas, etc.
    return re.sub(r"\s+", " ", t).strip()


def detectar(movimientos, excluidas=(), tipo_cambio: float | None = None) -> dict:
    """movimientos: objetos o dicts con fecha, descripcion, monto, moneda, categoria, entidad."""
    g = lambda m, k: m.get(k) if isinstance(m, dict) else getattr(m, k, None)
    grupos = defaultdict(list)
    for m in movimientos or []:
        monto, cat = g(m, "monto") or 0, g(m, "categoria")
        if monto >= 0 or cat in excluidas or cat in NO_RECURRENTES:
            continue
        if g(m, "moneda") == "USD" and not tipo_cambio:
            continue
        grupos[clave(g(m, "descripcion"))].append(m)

    out = []
    for ms in grupos.values():
        por_mes = defaultdict(list)
        for m in ms:
            v = -g(m, "monto") * (tipo_cambio if g(m, "moneda") == "USD" else 1)
            por_mes[g(m, "fecha")[:7]].append(v)
        meses = sorted(por_mes)
        suscripcion = g(ms[0], "categoria") == "Suscripciones"
        un_cobro = all(len(v) == 1 for v in por_mes.values())
        montos = [sum(por_mes[x]) for x in meses]
        med = statistics.median(montos)
        parecidos = all(abs(v - med) <= med * 0.4 for v in montos)
        if not suscripcion and not (len(meses) >= 2 and un_cobro and parecidos):
            continue
        ultimo = montos[-1]
        aumento = None
        if len(montos) >= 2:
            anterior = montos[-2]
            if anterior > 0 and ultimo - anterior >= AUMENTO_MIN_ARS and (ultimo / anterior - 1) * 100 >= AUMENTO_MIN_PCT:
                aumento = {"anterior": round(anterior, 2), "actual": round(ultimo, 2), "pct": round((ultimo / anterior - 1) * 100, 1),
                           "mes": meses[-1]}
        out.append({"descripcion": g(ms[-1], "descripcion"), "categoria": g(ms[0], "categoria"), "entidad": g(ms[-1], "entidad"),
                    "meses": len(meses), "ultimo_mes": meses[-1], "mensual": round(ultimo, 2), "anual": round(ultimo * 12, 2),
                    "suscripcion": suscripcion, "aumento": aumento})
    out.sort(key=lambda x: -x["mensual"])
    return {"pagos": out, "total_mensual": round(sum(x["mensual"] for x in out), 2),
            "aumentos": sum(1 for x in out if x["aumento"])}


def avisos(rec: dict, maximo: int = 3) -> list:
    fmt = lambda v: "$" + f"{v:,.0f}".replace(",", ".")
    subas = sorted((x for x in (rec or {}).get("pagos", []) if x["aumento"]), key=lambda x: -x["aumento"]["pct"])
    return [{"nivel": "media" if x["aumento"]["pct"] >= 20 else "baja", "tipo": "aumento",
             "titulo": f"{x['descripcion']} subió {x['aumento']['pct']:.0f}%".replace(".", ","),
             "detalle": f"De {fmt(x['aumento']['anterior'])} a {fmt(x['aumento']['actual'])} por mes ({fmt((x['aumento']['actual'] - x['aumento']['anterior']) * 12)} más por año)."}
            for x in subas[:maximo]]
