"""Galicia: 'Resumen de Caja de Ahorro en Pesos / en dolares' (extractos consolidados)."""
import re

from modelo import Cuenta, Movimiento
from .comun import ddmmyy, monto, verificar_saldos

ENTIDAD = "Galicia"
LINEA = re.compile(r"^\s*(\d{2}/\d{2}/\d{2})\s+(.+?)\s+(-?[\d.]+,\d{2})\s+(-?[\d.]+,\d{2})\s*$")
RUIDO = re.compile(r"resumen de caja|p[aá]gina|^fecha\b|^total\b|^varios$|^operacion\b|banco de galicia y b|^\d{10,}\w?$|^[A-Z0-9]{16,}$", re.I)


def detectar(t):
    return "Resumen de Caja de Ahorro en" in t and ("galicia" in t.lower())


def _detalle(lineas, i):
    """Primera línea útil debajo del movimiento (contraparte), antes de un blanco o de otra fecha."""
    for l in lineas[i + 1:i + 7]:
        s = l.strip()
        if not s or LINEA.match(l):
            return None
        if RUIDO.search(s) or not re.search(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]{3}", s) or re.fullmatch(r"[\d\s]+", s):
            continue
        return re.sub(r"\s{2,}", " ", s)
    return None


def parsear(t):
    from . import Resultado
    usd = bool(re.search(r"Caja de Ahorro en d[oó]lares", t, re.I))
    mon = "USD" if usd else "ARS"
    tipo = "Caja de ahorro en dólares" if usd else "Caja de ahorro en pesos"
    fechas = re.findall(r"\b(\d{2}/\d{2}/\d{4})\b", t)
    desde, hasta = (ddmmyy(fechas[0]), ddmmyy(fechas[1])) if len(fechas) >= 2 else (None, None)
    m_tit = re.search(r"^\s*([A-ZÁÉÍÓÚÑ ]{6,}?)\s{2,}CUIL", t, re.M)
    titular = re.sub(r"\s+", " ", m_tit[1]).strip() if m_tit else None

    lineas = t.splitlines()
    movs, pares = [], []
    for i, l in enumerate(lineas):
        m = LINEA.match(l)
        if not m:
            continue
        desc = re.split(r"\s{2,}", m[2].strip())[0]          # descarta la columna "Origen"
        det = _detalle(lineas, i)
        if det:
            desc = f"{desc} · {det}"
        imp, saldo = monto(m[3]), monto(m[4])
        movs.append(Movimiento(ddmmyy(m[1]), ENTIDAD, desc, imp, mon))
        pares.append((imp, saldo))

    saldo_final = None
    tot = re.search(r"^\s*Total\b.*?(?:\$|USD)\s*([\d.]+,\d{2})\s*$", t, re.M)
    if tot:
        saldo_final = monto(tot[1])
    elif pares:
        saldo_final = pares[-1][1]
    res = Resultado(ENTIDAD, f"{tipo} {desde or '?'} a {hasta or '?'}", titular=titular)
    if saldo_final is not None:
        res.cuentas.append(Cuenta(ENTIDAD, tipo, mon, saldo_final, hasta))
    res.movimientos = movs
    res.cobertura = {"entidad": ENTIDAD, "cuenta": tipo, "desde": desde, "hasta": hasta}
    if pares:
        ini = pares[0][1] - pares[0][0]
        if (n := verificar_saldos(pares, ini)):
            res.advertencias.append(f"Galicia {tipo}: {n} movimientos no cierran con el saldo; revisá el PDF.")
    return res
