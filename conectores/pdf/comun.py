import re

from utils import parse_monto

MONTO = r"-?\$?\s?-?[\d.]+,\d{2}"
MESES = {m: i for i, m in enumerate(["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                                     "septiembre", "octubre", "noviembre", "diciembre"], 1)}
MESES["setiembre"] = 9


def ddmmyy(s: str) -> str:
    d, m, a = re.split(r"[/-]", s)
    a = a if len(a) == 4 else "20" + a
    return f"{a}-{int(m):02d}-{int(d):02d}"


def monto(s: str) -> float:
    s = s.replace(" ", "")
    neg = "-" in s
    n = parse_monto(s.replace("-", ""))
    return -n if neg else n


def verificar_saldos(movs_con_saldo, saldo_inicial=None):
    """Chequea que cada saldo = saldo anterior + monto. Devuelve cantidad de diferencias."""
    errores, prev = 0, saldo_inicial
    for m, saldo in movs_con_saldo:
        if prev is not None and abs(prev + m - saldo) > 0.015:
            errores += 1
        prev = saldo
    return errores
