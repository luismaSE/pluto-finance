"""Avisos que se muestran en la app y en el dashboard: tarjetas por vencer, límites de gasto y
resúmenes viejos. Cada aviso: {"nivel": "alta"|"media"|"baja", "titulo", "detalle"}."""
from datetime import date


def _fmt(n):
    return "$ " + f"{n:,.0f}".replace(",", ".")


def generar(resumen: dict, tarjetas: list, presupuestos: dict, hoy: date | None = None) -> list[dict]:
    hoy = hoy or date.today()
    av = []
    for t in tarjetas or []:
        dv, dc = t.get("dias_vencimiento"), t.get("dias_cierre")
        if dv is not None and dv <= 7:
            av.append({"nivel": "alta" if dv <= 3 else "media", "tipo": "tarjeta",
                       "titulo": f"{t['nombre']} vence {'hoy' if dv == 0 else 'mañana' if dv == 1 else f'en {dv} días'}",
                       "detalle": f"Vencimiento el {t['proximo_vencimiento'][8:10]}/{t['proximo_vencimiento'][5:7]}."})
        if dc is not None and dc <= 3:
            av.append({"nivel": "baja", "tipo": "tarjeta",
                       "titulo": f"{t['nombre']} cierra {'hoy' if dc == 0 else 'mañana' if dc == 1 else f'en {dc} días'}",
                       "detalle": "Lo que compres después del cierre entra en el resumen siguiente."})
    p = (presupuestos or {}).get("meses", {}).get((presupuestos or {}).get("mes_actual"))
    if p:
        for it in ([p["total"]] if p.get("total") else []) + p.get("categorias", []):
            if it["estado"] == "excedido":
                av.append({"nivel": "alta", "tipo": "presupuesto", "titulo": f"Te pasaste del límite: {it['nombre']}",
                           "detalle": f"Gastaste {_fmt(it['gastado'])} de {_fmt(it['limite'])} ({it['pct']:.0f}%)."})
            elif it["estado"] == "cerca" or it.get("proyeccion_excede"):
                det = f"Llevás {_fmt(it['gastado'])} de {_fmt(it['limite'])} ({it['pct']:.0f}%)"
                if it.get("proyeccion_excede"):
                    det += f"; a este ritmo terminarías el mes en {_fmt(it['proyeccion'])}"
                titulo = f"Cerca del límite: {it['nombre']}" if it["estado"] == "cerca" else f"A este ritmo te pasás: {it['nombre']}"
                av.append({"nivel": "media", "tipo": "presupuesto", "titulo": titulo, "detalle": det + "."})
    viejos = {}
    for x in (resumen.get("liquidez") or []) + (resumen.get("inversiones") or []):
        if x.get("al"):
            dias = (hoy - date.fromisoformat(x["al"])).days
            viejos[x["entidad"]] = min(dias, viejos.get(x["entidad"], dias))
    for ent, dias in viejos.items():
        if dias > 35:
            av.append({"nivel": "baja", "tipo": "datos", "titulo": f"Resumen de {ent} desactualizado",
                       "detalle": f"Los datos son de hace {dias} días. Descargá el resumen nuevo."})
    orden = {"alta": 0, "media": 1, "baja": 2}
    return sorted(av, key=lambda a: orden[a["nivel"]])
