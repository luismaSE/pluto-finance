"""IOL (InvertirOnline) - API oficial.

Las credenciales se piden en la terminal y solo viven en memoria durante el login.
El token obtenido se descarta al terminar. Nada se escribe a disco.
Requisito: tener habilitado el acceso por API en IOL (Mi cuenta > Personalización > APIs).
"""
import getpass

import requests

from modelo import Cuenta, Inversion
from utils import normalizar_moneda

BASE = "https://api.invertironline.com"

# --- metadatos para el registro de brokers ---
ID = "iol"
NOMBRE = "IOL"
DESCRIPCION = "InvertirOnline (API oficial). Habilitá el acceso por API en Mi cuenta → Personalización → APIs."
CAMPOS = [  # se piden en cada actualización; los marcados "secreto" nunca se guardan
    {"id": "usuario", "etiqueta": "Usuario"},
    {"id": "clave", "etiqueta": "Clave", "secreto": True},
]


def _login(usuario: str | None = None, clave: str | None = None) -> str:
    if not usuario:
        usuario = input("IOL - usuario: ").strip()
    if not clave:
        clave = getpass.getpass("IOL - clave (no se muestra): ")
    try:
        r = requests.post(
            f"{BASE}/token",
            data={"username": usuario, "password": clave, "grant_type": "password"},
            timeout=30,
        )
    finally:
        del clave
    if r.status_code != 200:
        raise RuntimeError(f"Login IOL rechazado ({r.status_code}). ¿Usuario/clave correctos y API habilitada?")
    return r.json()["access_token"]


def obtener(credenciales: dict | None = None, clave: str | None = None):
    """credenciales = {"usuario": ..., "clave": ...}. Devuelve (cuentas, movimientos, inversiones)."""
    if isinstance(credenciales, str):          # compatibilidad: obtener(usuario, clave)
        credenciales = {"usuario": credenciales, "clave": clave}
    credenciales = credenciales or {}
    token = _login(credenciales.get("usuario"), credenciales.pop("clave", None))
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {token}"
    cuentas, inversiones = [], []
    try:
        est = s.get(f"{BASE}/api/v2/estadocuenta", timeout=30)
        est.raise_for_status()
        for c in est.json().get("cuentas", []):
            moneda = normalizar_moneda(c.get("moneda")) or "ARS"
            disponible = float(c.get("disponible") or 0)
            if disponible == 0 and not c.get("titulosValorizados"):
                continue
            mercado = "EE.UU." if "estados" in str(c.get("tipo", "")).lower() else "Argentina"
            cuentas.append(Cuenta(NOMBRE, f"Disponible para operar ({mercado})", moneda, disponible))

        for pais in ("argentina", "estados_Unidos"):
            r = s.get(f"{BASE}/api/v2/portafolio/{pais}", timeout=30)
            if r.status_code != 200:
                continue
            for a in r.json().get("activos", []):
                t = a.get("titulo", {}) or {}
                inversiones.append(Inversion(
                    entidad=NOMBRE,
                    activo=t.get("simbolo", "?"),
                    descripcion=t.get("descripcion", ""),
                    tipo=str(t.get("tipo", "")).upper(),
                    cantidad=float(a.get("cantidad") or 0),
                    valuacion=float(a.get("valorizado") or 0),
                    moneda=normalizar_moneda(t.get("moneda")) or "ARS",
                    variacion_dia_pct=a.get("variacionDiaria"),
                    ganancia_pct=a.get("gananciaPorcentaje"),
                    ganancia=a.get("gananciaDinero"),
                ))
    finally:
        s.headers.pop("Authorization", None)
        del token
    return cuentas, [], inversiones
