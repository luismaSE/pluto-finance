"""Cotizaciones del dólar desde dolarapi.com (pública, sin credenciales)."""
import requests

from utils import parse_monto

CASAS = {"oficial": "oficial", "mep": "bolsa", "ccl": "contadoconliqui", "blue": "blue"}


def obtener() -> dict:
    cot = {}
    for nombre, casa in CASAS.items():
        try:
            r = requests.get(f"https://dolarapi.com/v1/dolares/{casa}", timeout=10)
            r.raise_for_status()
            d = r.json()
            cot[nombre] = {"compra": d.get("compra"), "venta": d.get("venta")}
        except Exception:
            pass
    if "mep" not in cot:
        try:
            v = input("No pude obtener el dólar MEP. Ingresalo a mano (Enter para omitir): ").strip()
        except EOFError:
            v = ""
        if parse_monto(v):
            cot["mep"] = {"compra": parse_monto(v), "venta": parse_monto(v), "manual": True}
    return cot
