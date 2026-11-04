"""Galicia: posición de cuenta comitente (Fondos FIMA y otras tenencias valorizadas)."""
import re

from modelo import Inversion
from utils import parse_monto
from .comun import ddmmyy

ENTIDAD = "Galicia"
# FONDO EJEMPLO CLASE A      1.000,00  $ 100,000000  $ 100.000,00
LINEA = re.compile(r"^\s*(\S.*?)\s{2,}([\d.]+,\d+)\s*(\$|USD)\s*([\d.]+,\d+)\s*(\$|USD)\s*([\d.]+,\d{2})\s*$")


def detectar(t):
    return "Saldo Valorizado" in t and ("Posicion al" in t or "Posición al" in t)


def parsear(t):
    from . import Resultado
    m = re.search(r"Posici[oó]n al\s+(\d{2}/\d{2}/\d{4})", t)
    al = ddmmyy(m[1]) if m else None
    seccion, invs = "", []
    for l in t.splitlines():
        s = l.strip()
        if s.isupper() and "-" in s and not LINEA.match(l):   # ej. "FIMA-FONDOS COMUNES DE INVERSION"
            seccion = s
        mm = LINEA.match(l)
        if not mm:
            continue
        nombre = mm[1].strip()
        tipo = "FCI" if ("FONDO" in seccion.upper() or "FIMA" in nombre.upper()) else "TÍTULOS"
        invs.append(Inversion(ENTIDAD, nombre.title().replace("Fima", "FIMA"), nombre, tipo,
                              parse_monto(mm[2]) or 0, parse_monto(mm[6]) or 0,
                              "USD" if mm[5] == "USD" else "ARS", al=al))
    res = Resultado(ENTIDAD, f"Posición de inversiones al {al or '?'}")
    res.inversiones = invs
    if not invs:
        res.advertencias.append("Galicia: el PDF de posición no tiene tenencias reconocibles.")
    return res
