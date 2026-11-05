"""Límites de gasto mensuales, total y por categoría.

    [presupuestos]
    total = 900000                  # 0 = sin límite total
    [presupuestos.categorias]
    "Delivery y restaurantes" = 60000
    Supermercado = 350000
"""
import calendar
from datetime import date


def _estado(pct: float) -> str:
    return "excedido" if pct >= 100 else "cerca" if pct >= 80 else "ok"


def _item(nombre, limite, gastado, factor):
    pct = gastado / limite * 100 if limite else 0
    proy = gastado * factor if factor else None
    return {"nombre": nombre, "limite": limite, "gastado": gastado, "pct": pct, "estado": _estado(pct),
            "restante": limite - gastado, "proyeccion": proy,
            "proyeccion_excede": bool(proy and proy > limite)}


def evaluar(cfg: dict, gastos_por_mes: dict, hoy: date | None = None) -> dict:
    """Devuelve, por mes, el avance contra cada límite. En el mes actual agrega la proyección a fin de mes."""
    hoy = hoy or date.today()
    total = float((cfg or {}).get("total") or 0)
    cats = {k: float(v) for k, v in ((cfg or {}).get("categorias") or {}).items() if v}
    if not total and not cats:
        return {"configurado": False, "meses": {}}
    meses = {}
    for mes, g in (gastos_por_mes or {}).items():
        factor = None
        # Proyección a fin de mes solo en el mes actual y desde el día 7 (antes es demasiado imprecisa)
        if mes == hoy.strftime("%Y-%m") and hoy.day >= 7:
            factor = calendar.monthrange(hoy.year, hoy.month)[1] / hoy.day
        meses[mes] = {
            "total": _item("Total", total, g.get("total_ars", 0), factor) if total else None,
            "categorias": [_item(c, lim, g.get("por_categoria", {}).get(c, 0), factor) for c, lim in cats.items()],
        }
    return {"configurado": True, "meses": meses, "mes_actual": hoy.strftime("%Y-%m")}
