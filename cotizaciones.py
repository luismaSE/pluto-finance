"""Cotizaciones del dólar (dolarapi.com) y referencias de tasas e inflación (argentinadatos.com).
APIs públicas, sin credenciales."""
import requests

from utils import parse_monto

CASAS = {"oficial": "oficial", "mep": "bolsa", "ccl": "contadoconliqui", "blue": "blue"}


def obtener(pedir_mep=True) -> dict:
    cot = {}
    for nombre, casa in CASAS.items():
        try:
            r = requests.get(f"https://dolarapi.com/v1/dolares/{casa}", timeout=10)
            r.raise_for_status()
            d = r.json()
            cot[nombre] = {"compra": d.get("compra"), "venta": d.get("venta")}
        except Exception:
            pass
    if "mep" not in cot and pedir_mep:
        try:
            v = input("No pude obtener el dólar MEP. Ingresalo a mano (Enter para omitir): ").strip()
        except EOFError:
            v = ""
        if parse_monto(v):
            cot["mep"] = {"compra": parse_monto(v), "venta": parse_monto(v), "manual": True}
    return cot


def _tasa(v):
    """Acepta 0.29 o 29 y devuelve 0.29."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v / 100 if v > 1 else v


def referencias(config_ref: dict | None = None) -> dict:
    """TNA de plazo fijo (promedio de los bancos que informan) e inflación del último mes.
    Si la API no responde se usan los valores de config.toml [referencias]."""
    cfg = config_ref or {}
    ref = {}
    try:
        r = requests.get("https://api.argentinadatos.com/v1/finanzas/tasas/plazoFijo", timeout=10)
        r.raise_for_status()
        tasas = [t for t in (_tasa(x.get("tnaClientes")) for x in r.json()) if t]
        if tasas:
            ref["tna_plazo_fijo"] = sum(tasas) / len(tasas)
            ref["tna_fuente"] = f"promedio de {len(tasas)} bancos (argentinadatos.com)"
    except Exception:
        pass
    try:
        r = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/inflacion", timeout=10)
        r.raise_for_status()
        ult = sorted(r.json(), key=lambda x: x.get("fecha", ""))[-1]
        ref["inflacion_mensual"] = float(ult["valor"]) / 100
        ref["inflacion_mes"] = str(ult["fecha"])[:7]
    except Exception:
        pass
    if "tna_plazo_fijo" not in ref and _tasa(cfg.get("tna_plazo_fijo")):
        ref["tna_plazo_fijo"] = _tasa(cfg["tna_plazo_fijo"])
        ref["tna_fuente"] = "valor cargado en la configuración"
    if "inflacion_mensual" not in ref and _tasa(cfg.get("inflacion_mensual")):
        ref["inflacion_mensual"] = _tasa(cfg["inflacion_mensual"])
        ref["inflacion_mes"] = "configuración"
    return ref
