"""IOL (InvertirOnline) - API oficial. SOLO LECTURA.

Pluto nunca opera: después del login, la conexión solo permite consultas (GET). Cualquier otro
pedido (comprar, vender, transferir) se rechaza antes de salir de la computadora.

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


class SoloLectura(requests.Session):
    """Sesión que solo deja hacer consultas. Pluto no puede operar en la cuenta."""

    def request(self, method, url, *args, **kwargs):
        if str(method).upper() != "GET":
            raise PermissionError(f"Pluto solo consulta datos: se bloqueó un pedido {method} a IOL")
        return super().request(method, url, *args, **kwargs)


MERCADOS = {"bcba": "bCBA", "nyse": "nYSE", "nasdaq": "nASDAQ", "amex": "aMEX", "rofx": "rOFX"}


def _mercado(m: str | None) -> str:
    return MERCADOS.get(str(m or "bcba").lower().replace("_", ""), "bCBA")


def _precios(s: requests.Session, simbolos: list[tuple[str, str]], dias: int = 400) -> dict:
    """Cotización actual y serie diaria (último año) de cada símbolo. Los errores se saltean."""
    from datetime import date, timedelta
    hasta, desde = date.today(), date.today() - timedelta(days=dias)
    out = {}
    for simbolo, mercado in simbolos:
        if not simbolo or simbolo in out:
            continue
        item = {"mercado": mercado}
        try:
            r = s.get(f"{BASE}/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion", timeout=20)
            if r.status_code == 200:
                c = r.json()
                item.update(precio=c.get("ultimoPrecio"), variacion_dia=c.get("variacion"),
                            moneda=normalizar_moneda(c.get("moneda")) or "ARS", fecha=str(c.get("fechaHora", ""))[:10])
            r = s.get(f"{BASE}/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/"
                      f"{desde.isoformat()}/{hasta.isoformat()}/ajustada", timeout=30)
            if r.status_code == 200:
                serie = sorted({str(x.get("fechaHora", ""))[:10]: x.get("ultimoPrecio") for x in r.json()
                                if x.get("ultimoPrecio")}.items())
                item["serie"] = [[f, p] for f, p in serie]
        except Exception:
            pass
        if item.get("precio") or item.get("serie"):
            out[simbolo] = item
    return out


def obtener(credenciales: dict | None = None, clave: str | None = None, extra: dict | None = None):
    """credenciales = {"usuario": ..., "clave": ...}. Devuelve (cuentas, movimientos, inversiones).
    Si se pasa `extra` con extra["mercado"] = True, agrega extra["precios"] con cotizaciones y series
    de las tenencias y de extra["seguimiento"] (lista de símbolos, "SIMBOLO" o "SIMBOLO:mercado")."""
    if isinstance(credenciales, str):          # compatibilidad: obtener(usuario, clave)
        credenciales = {"usuario": credenciales, "clave": clave}
    credenciales = credenciales or {}
    token = _login(credenciales.get("usuario"), credenciales.pop("clave", None))
    s = SoloLectura()
    s.headers["Authorization"] = f"Bearer {token}"
    cuentas, inversiones, mercados_tenencia = [], [], {}
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
                mercados_tenencia[t.get("simbolo", "?")] = _mercado(t.get("mercado"))
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
        if extra is not None and extra.get("mercado"):
            simbolos = list(mercados_tenencia.items())
            for x in extra.get("seguimiento") or []:
                sim, _, mer = str(x).strip().upper().partition(":")
                simbolos.append((sim, _mercado(mer or "bcba")))
            extra["precios"] = _precios(s, simbolos)
    finally:
        s.headers.pop("Authorization", None)
        del token
    return cuentas, [], inversiones
