"""Fechas de cierre y vencimiento de las tarjetas de crédito.

Se configuran en config.toml (o en la app):
    [tarjetas.visa_galicia]
    nombre = "Visa Galicia"
    cierre = 24              # día del mes en que cierra el resumen
    vencimiento = 6          # día del mes en que vence el pago
    proximo_cierre = ""      # opcional: fecha exacta (AAAA-MM-DD) si el banco la corre
    proximo_vencimiento = ""

Los bancos suelen mover las fechas unos días cada mes; si cargás la fecha exacta del resumen, se usa esa.
"""
import calendar
from datetime import date, timedelta


def _dia_en_mes(anio: int, mes: int, dia: int) -> date:
    return date(anio, mes, min(max(int(dia), 1), calendar.monthrange(anio, mes)[1]))


def proxima_fecha(dia: int, hoy: date) -> date:
    """Próxima fecha (hoy incluido) que cae en el día `dia` del mes (31 → último día en meses cortos)."""
    d = _dia_en_mes(hoy.year, hoy.month, dia)
    if d >= hoy:
        return d
    anio, mes = (hoy.year + 1, 1) if hoy.month == 12 else (hoy.year, hoy.month + 1)
    return _dia_en_mes(anio, mes, dia)


def _fecha_exacta(texto, hoy: date) -> date | None:
    try:
        d = date.fromisoformat(str(texto).strip())
        return d if d >= hoy else None       # una fecha exacta vieja se ignora y vuelve al día del mes
    except ValueError:
        return None


def _ultimo_pago(nombre: str, movimientos) -> dict | None:
    """Último débito "pago tarjeta ..." que coincide con la marca de la tarjeta (visa, master, amex)."""
    marcas = [m for m in ("visa", "master", "amex", "american", "naranja", "cabal") if m in nombre.lower()]
    pagos = []
    for m in movimientos or []:
        desc = (m.get("descripcion") if isinstance(m, dict) else m.descripcion).lower()
        monto = m.get("monto") if isinstance(m, dict) else m.monto
        fecha = m.get("fecha") if isinstance(m, dict) else m.fecha
        if "tarjeta" in desc and "pago" in desc and monto < 0 and (not marcas or any(k in desc for k in marcas)):
            pagos.append({"fecha": fecha, "monto": -monto, "moneda": m.get("moneda") if isinstance(m, dict) else m.moneda})
    return max(pagos, key=lambda p: p["fecha"]) if pagos else None


def calcular(cfg_tarjetas: dict, hoy: date | None = None, movimientos=None) -> list[dict]:
    hoy = hoy or date.today()
    out = []
    for tid, t in (cfg_tarjetas or {}).items():
        if not isinstance(t, dict) or not (t.get("cierre") or t.get("proximo_cierre") or t.get("vencimiento") or t.get("proximo_vencimiento")):
            continue
        cierre = _fecha_exacta(t.get("proximo_cierre", ""), hoy) or (proxima_fecha(t["cierre"], hoy) if t.get("cierre") else None)
        venc = _fecha_exacta(t.get("proximo_vencimiento", ""), hoy) or (proxima_fecha(t["vencimiento"], hoy) if t.get("vencimiento") else None)
        nombre = t.get("nombre") or tid
        out.append({
            "id": tid, "nombre": nombre, "entidad": t.get("entidad", ""),
            "proximo_cierre": cierre.isoformat() if cierre else None,
            "proximo_vencimiento": venc.isoformat() if venc else None,
            "dias_cierre": (cierre - hoy).days if cierre else None,
            "dias_vencimiento": (venc - hoy).days if venc else None,
            "ultimo_pago": _ultimo_pago(nombre, movimientos),
            # días del mes configurados: el dashboard recalcula la próxima fecha si se abre días después
            "cierre_dia": t.get("cierre") or None, "vencimiento_dia": t.get("vencimiento") or None,
        })
    return sorted(out, key=lambda x: min(d for d in (x["dias_vencimiento"], x["dias_cierre"], 999) if d is not None))
