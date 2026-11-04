"""Mercado Pago: 'Resumen de cuenta' (account_statement-*.pdf)."""
import re
from datetime import date

from modelo import Cuenta, Movimiento
from .comun import ddmmyy, monto, verificar_saldos, MESES

ENTIDAD = "Mercado Pago"
# [prefijo] 05-10-2026   Transferencia enviada Comercio   123456789012   $ -1.500,00   $ 10.000,00
LINEA = re.compile(r"^\s*(\d{2}-\d{2}-\d{4})\s+(.*?)\s+(\d{6,})\s+(\$\s?-?[\d.]+,\d{2})\s+(\$\s?-?[\d.]+,\d{2})\s*$")
RUIDO = re.compile(r"^(fecha\b|operaci[oó]n$|\d+/\d+$|fecha de generaci|mercado libre s\.r\.l|de consulta|detalle de movimientos)", re.I)
INICIO = re.compile(r"^(transferencia|pago|rendimiento|ingreso|extracci|compra|devoluci|reintegro|d[eé]bito|cobro|recarga|env[ií]o|retiro|dinero|venta|cashback|reembolso|liberaci)", re.I)


def detectar(t):
    return "RESUMEN DE CUENTA" in t.upper() and "mercadopago" in t.lower().replace(" ", "")


def _periodo(t, movs):
    m = re.search(r"Del\s+(\d{1,2})(?:\s+de\s+(\w+)(?:\s+de\s+(\d{4}))?)?\s+al\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", t, re.I)
    if m:
        a2, m2 = int(m[6]), MESES.get(m[5].lower())
        m1 = MESES.get((m[2] or m[5]).lower())
        a1 = int(m[3] or a2)
        if m1 and m2:
            return date(a1, m1, int(m[1])).isoformat(), date(a2, m2, int(m[4])).isoformat()
    fechas = sorted(x.fecha for x in movs)
    return (fechas[0], fechas[-1]) if fechas else (None, None)


def parsear(t):
    from . import Resultado
    usd = "DÓLARES" in t.upper() or "DOLARES" in t.upper()
    mon = "USD" if usd else "ARS"
    lineas = t.splitlines()
    m_tit = next((i for i, l in enumerate(lineas) if "RESUMEN DE CUENTA" in l.upper()), None)
    titular = next((l.strip() for l in lineas[m_tit + 1:m_tit + 4] if l.strip()), None) if m_tit is not None else None

    movs, pares, prefijo, ultimo = [], [], "", None
    for l in lineas:
        s = re.sub(r"\s{2,}", " ", l.strip())
        mm = LINEA.match(l)
        if mm:
            desc = " ".join(x for x in (prefijo, re.sub(r"\s{2,}", " ", mm[2].strip())) if x)
            imp, saldo = monto(mm[4]), monto(mm[5])
            ultimo = Movimiento(ddmmyy(mm[1]), ENTIDAD, desc, imp, mon)
            movs.append(ultimo)
            pares.append((imp, saldo))
            prefijo = ""
            continue
        if not s or RUIDO.search(s) or ":" in s:
            continue
        if INICIO.match(s):
            prefijo = s              # descripción partida que sigue en la línea con la fecha
        elif ultimo is not None and not prefijo:
            ultimo.descripcion += " " + s

    sf = re.search(r"Saldo final:\s*(\$\s?-?[\d.]+,\d{2})", t)
    si = re.search(r"Saldo inicial:\s*(\$\s?-?[\d.]+,\d{2})", t)
    saldo_final = monto(sf[1]) if sf else (pares[-1][1] if pares else None)
    desde, hasta = _periodo(t, movs)
    res = Resultado(ENTIDAD, f"Resumen de cuenta {desde or '?'} a {hasta or '?'}", titular=titular)
    if saldo_final is not None:
        res.cuentas.append(Cuenta(ENTIDAD, "Dinero en cuenta", mon, saldo_final, hasta))
    res.movimientos = movs
    res.cobertura = {"entidad": ENTIDAD, "cuenta": "Dinero en cuenta", "desde": desde, "hasta": hasta}
    if pares and (n := verificar_saldos(pares, monto(si[1]) if si else None)):
        res.advertencias.append(f"Mercado Pago: {n} movimientos no cierran con el saldo; revisá el PDF.")
    return res
