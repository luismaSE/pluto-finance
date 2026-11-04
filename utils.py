import re
import unicodedata


def sin_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def clave(k: str) -> str:
    """Normaliza un nombre de campo JSON: 'Saldo_Disponible' -> 'saldodisponible'."""
    return re.sub(r"[^a-z0-9]", "", sin_acentos(str(k)).lower())


def parse_monto(v) -> float | None:
    """Convierte '$ 1.234,56', '-1,234.56', 'U$S 10' o números a float."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    neg = s.startswith("-") or s.endswith("-") or (s.startswith("(") and s.endswith(")"))
    s = re.sub(r"[^0-9.,]", "", s)
    if not s or not re.search(r"\d", s):
        return None
    if "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        mil = "." if dec == "," else ","
        s = s.replace(mil, "").replace(dec, ".")
    elif "," in s:
        partes = s.split(",")
        s = s.replace(",", ".") if len(partes) == 2 and len(partes[1]) <= 2 else s.replace(",", "")
    elif s.count(".") > 1 or re.fullmatch(r"\d{1,3}\.\d{3}", s):
        s = s.replace(".", "")
    try:
        n = float(s)
    except ValueError:
        return None
    return -n if neg else n


def normalizar_moneda(v) -> str | None:
    if v is None:
        return None
    s = clave(v)
    if s in {"ars", "pesos", "peso", "pesoargentino", "1", "032", "ar"} or s.startswith("peso") or s == "$":
        return "ARS"
    if s in {"usd", "us", "dolares", "dolar", "dolarestadounidense", "2", "840", "uss", "u"} or "dolar" in s:
        return "USD"
    raw = str(v).strip().upper()
    if raw in {"$", "AR$"}:
        return "ARS"
    if raw in {"U$S", "US$", "U$D", "USD$"}:
        return "USD"
    return None


def fecha_iso(v) -> str | None:
    """Acepta '2026-11-03T10:00:00', '03/11/2026', '03-11-2026', timestamps ms."""
    if v is None:
        return None
    if isinstance(v, (int, float)) and v > 1e9:
        from datetime import datetime
        ts = v / 1000 if v > 1e11 else v
        return datetime.fromtimestamp(ts).date().isoformat()
    s = str(v).strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m[1]}-{m[2]}-{m[3]}"
    m = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", s)
    if m:
        a = m[3] if len(m[3]) == 4 else "20" + m[3]
        return f"{a}-{int(m[2]):02d}-{int(m[1]):02d}"
    return None
