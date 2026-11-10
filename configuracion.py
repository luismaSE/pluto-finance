"""Configuración local.

- Datos que no son secretos -> config.toml (no se sube al repo).
- Secretos (tokens, contraseña del celular) -> llavero del sistema operativo
  (GNOME Keyring / KWallet en Linux, Credential Manager en Windows, Keychain en macOS).
  Nunca se escriben en archivos del proyecto.
"""
import copy
import re
import tomllib
from pathlib import Path

ARCHIVO = Path("config.toml")
SERVICIO = "pluto"
SERVICIO_ANTERIOR = "wallet-dashboard"   # nombre del llavero hasta la versión 1.2

DEFAULT = {
    "ui": {"tema": "dark"},
    "fuentes": {"reportes": "reportes", "descargas": "~/Descargas", "importar_descargas": True},
    # brokers con API: se activan acá y sus credenciales se piden en cada actualización
    "brokers": {"iol": {"activo": False}},
    # proveedor: "claude_code", "anthropic", "openai_compatible" u "ollama" (ver ia/)
    "analisis": {
        "activado": True,
        "proveedor": "claude_code",
        "claude_code": {"modelo": ""},
        "anthropic": {"modelo": "claude-opus-5-5"},
        "openai_compatible": {"modelo": "", "url": "https://api.openai.com/v1"},
        "ollama": {"modelo": "llama3.1", "url": "http://localhost:11434"},
    },
    # navegador para la descarga asistida: "chromium" (el de Playwright), "chrome", "msedge" o la ruta a un ejecutable
    "descarga": {"navegador": "chromium"},
    "referencias": {"tna_plazo_fijo": 0.0, "inflacion_mensual": 0.0},
    # Límites de gasto mensuales (0 = sin límite) y metas
    "presupuestos": {"total": 0, "categorias": {}},
    "metas": {"fondo_emergencia_meses": 6},
    # Metas de ahorro: {"viaje": {"nombre": "Viaje", "monto": 3000, "moneda": "USD", "fecha": "2027-07-01", "ahorrado": 800}}
    "objetivos": {},
    # Tarjetas: {"visa_galicia": {"nombre": "Visa Galicia", "cierre": 24, "vencimiento": 6}}
    "tarjetas": {},
    # Reglas propias de categoría: {"transferencia enviada verduleria don pepe": "Supermercado"}
    "categorias": {"reglas": {}},
    # Análisis de mercado (solo lectura: analiza y recomienda, nunca opera)
    # seguimiento: activos que no tenés pero querés seguir, ej. ["SPY", "AL30", "AAPL:nyse"]
    "mercado": {"activado": False, "perfil": "moderado", "horizonte_anios": 5, "seguimiento": [], "noticias": True},
    "privacidad": {"conservar_dashboards": 5, "cifrar_datos_locales": True},
    "publicar": {
        "destino": "ninguno",
        "github": {"repo": "", "ruta": "cartera.enc", "rama": "main", "token_env": "CARTERA_GITHUB_TOKEN"},
        "drive": {"client_secret": "client_secret.json", "nombre": "cartera.enc"},
    },
}

# Secretos que la app puede guardar en el llavero
SECRETOS = {
    "github_token": "Token de GitHub (escritura en el repo de datos)",
    "celular_password": "Contraseña de cifrado del celular",
    "ia_anthropic": "Clave de API de Anthropic",
    "ia_openai": "Clave de la API compatible con OpenAI",
}


def primer_uso() -> bool:
    """True si todavía no hay configuración (se muestra el asistente de bienvenida)."""
    return not ARCHIVO.exists()


def _mezclar(base, extra):
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _mezclar(base[k], v)
        else:
            base[k] = v
    return base


def _migrar(cfg: dict, archivo: dict):
    """Convierte configuraciones de versiones anteriores."""
    f = archivo.get("fuentes", {})
    if "iol" in f and "brokers" not in archivo:            # antes: fuentes.iol = true/false
        cfg["brokers"]["iol"]["activo"] = bool(f["iol"])
    cfg["fuentes"].pop("iol", None)
    a = archivo.get("analisis", {})
    if isinstance(a.get("modelo"), str) and "proveedor" not in a:   # antes: analisis.modelo (Claude Code)
        cfg["analisis"]["claude_code"]["modelo"] = a["modelo"]
    cfg["analisis"].pop("modelo", None)


def cargar() -> dict:
    cfg = copy.deepcopy(DEFAULT)
    if ARCHIVO.exists():
        with ARCHIVO.open("rb") as f:
            archivo = tomllib.load(f)
        _mezclar(cfg, archivo)
        _migrar(cfg, archivo)
    return cfg


def _valor(v):
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_valor(x) for x in v) + "]"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _clave(k) -> str:
    """Claves TOML: sin comillas si son simples, entre comillas si tienen espacios o acentos."""
    k = str(k)
    return k if re.fullmatch(r"[A-Za-z0-9_-]+", k) else _valor(k)


def _escribir(d, prefijo, lineas):
    simples = {k: v for k, v in d.items() if not isinstance(v, dict)}
    vacia = not d
    if prefijo and (simples or vacia):
        lineas.append(f"\n[{prefijo}]")
    for k, v in simples.items():
        lineas.append(f"{_clave(k)} = {_valor(v)}")
    for k, v in d.items():
        if isinstance(v, dict):
            _escribir(v, f"{prefijo}.{_clave(k)}" if prefijo else _clave(k), lineas)


def guardar(cfg: dict):
    lineas = ["# Configuración de Pluto (generado por la app; no contiene secretos)"]
    _escribir(cfg, "", lineas)
    ARCHIVO.write_text("\n".join(lineas) + "\n", encoding="utf-8")


# ---------- llavero ----------
def _keyring():
    try:
        import keyring
        return keyring
    except ImportError:
        return None


def llavero_disponible() -> tuple[bool, str]:
    kr = _keyring()
    if kr is None:
        return False, "Falta la librería keyring (pip install keyring)"
    try:
        backend = kr.get_keyring()
        nombre = type(backend).__name__
        if "fail" in nombre.lower() or "null" in nombre.lower():
            return False, "No hay un llavero del sistema disponible (instalá gnome-keyring o kwallet)"
        return True, nombre
    except Exception as e:
        return False, str(e)


def leer_secreto(nombre: str) -> str | None:
    kr = _keyring()
    if not kr:
        return None
    try:
        v = kr.get_password(SERVICIO, nombre)
        if v is None:
            # Migración: secretos guardados con el nombre anterior del llavero
            v = kr.get_password(SERVICIO_ANTERIOR, nombre)
            if v is not None:
                kr.set_password(SERVICIO, nombre, v)
                try:
                    kr.delete_password(SERVICIO_ANTERIOR, nombre)
                except Exception:
                    pass
        return v
    except Exception:
        return None


def guardar_secreto(nombre: str, valor: str):
    kr = _keyring()
    if not kr:
        raise RuntimeError("keyring no está instalado")
    kr.set_password(SERVICIO, nombre, valor)


def borrar_secreto(nombre: str):
    kr = _keyring()
    if kr:
        for servicio in (SERVICIO, SERVICIO_ANTERIOR):
            try:
                kr.delete_password(servicio, nombre)
            except Exception:
                pass
