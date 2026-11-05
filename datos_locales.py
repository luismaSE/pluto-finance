"""Archivos con datos personales que quedan en la PC (historial, último análisis).

Si [privacidad] cifrar_datos_locales = true y hay llavero, se guardan cifrados con AES-256-GCM
usando una clave aleatoria que vive en el llavero del sistema (nunca en un archivo). Sin llavero
se guardan como JSON común. Los archivos viejos sin cifrar se leen igual y se cifran al reescribirlos.
"""
import base64
import json
import os
from pathlib import Path

SECRETO = "datos_locales"


def _cifrar_activado() -> bool:
    try:
        import configuracion
        return bool(configuracion.cargar()["privacidad"].get("cifrar_datos_locales", True))
    except Exception:
        return False


def _clave(crear: bool) -> bytes | None:
    import configuracion
    ok, _ = configuracion.llavero_disponible()
    if not ok:
        return None
    k = configuracion.leer_secreto(SECRETO)
    if not k and crear:
        k = base64.b64encode(os.urandom(32)).decode()
        try:
            configuracion.guardar_secreto(SECRETO, k)
        except Exception:
            return None
    return base64.b64decode(k) if k else None


def escribir(ruta: Path, obj) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(obj, ensure_ascii=False, indent=1, default=str)
    clave = _clave(crear=True) if _cifrar_activado() else None
    if clave:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        iv = os.urandom(12)
        ct = AESGCM(clave).encrypt(iv, texto.encode("utf-8"), None)
        texto = json.dumps({"pluto_local": 1, "iv": base64.b64encode(iv).decode(), "ct": base64.b64encode(ct).decode()})
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    tmp.write_text(texto, encoding="utf-8")
    tmp.replace(ruta)


def leer(ruta: Path, defecto=None):
    try:
        obj = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except Exception:
        return defecto
    if isinstance(obj, dict) and obj.get("pluto_local") == 1:
        clave = _clave(crear=False)
        if not clave:
            return defecto          # cifrado con una clave que este equipo ya no tiene
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            plano = AESGCM(clave).decrypt(base64.b64decode(obj["iv"]), base64.b64decode(obj["ct"]), None)
            return json.loads(plano)
        except Exception:
            return defecto
    return obj


def limpiar_dashboards(carpeta: str = "salida", conservar: int | None = None) -> int:
    """Borra los dashboards más viejos y deja los últimos `conservar`. Devuelve cuántos borró."""
    if conservar is None:
        try:
            import configuracion
            conservar = int(configuracion.cargar()["privacidad"].get("conservar_dashboards", 5))
        except Exception:
            conservar = 5
    conservar = max(1, conservar)
    archivos = sorted(Path(carpeta).glob("dashboard_*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in archivos[conservar:]:
        p.unlink(missing_ok=True)
    return max(0, len(archivos) - conservar)
