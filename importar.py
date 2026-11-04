"""Incorpora resúmenes PDF a la carpeta reportes/.

Reconoce cada PDF por su contenido (no por el nombre) y lleva un índice con la huella
SHA-256 de cada archivo para no importar dos veces el mismo resumen.
Lo usan la importación desde Descargas y la descarga asistida desde Galicia / Mercado Pago.
"""
import hashlib
import json
import shutil
import time
from pathlib import Path

from conectores import pdf

INDICE = ".indice.json"


def _huella(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _cargar_indice(dest: Path) -> dict:
    f = dest / INDICE
    idx = json.loads(f.read_text()) if f.exists() else {}
    conocidos = {v.get("archivo") for v in idx.values()}
    for p in dest.glob("*.pdf"):          # PDFs que ya estaban en reportes/
        if p.name not in conocidos:
            idx[_huella(p)] = {"archivo": p.name}
    return idx


def _guardar_indice(dest: Path, idx: dict):
    (dest / INDICE).write_text(json.dumps(idx, indent=1, ensure_ascii=False))


def _nombre(r) -> str:
    cob = r.cobertura or {}
    sufijo = cob.get("hasta") or (r.inversiones[0].al if r.inversiones else None) or time.strftime("%Y-%m-%d")
    base = f"{r.entidad}_{(cob.get('cuenta') or r.descripcion.split(' al ')[0])}_{sufijo}"
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in base).strip("_") + ".pdf"


def incorporar(archivo: Path, reportes: str, log=print, _idx: dict | None = None) -> str | None:
    """Copia un PDF a reportes/ si es un resumen reconocido y no estaba. Devuelve el nombre nuevo o None."""
    dest = Path(reportes).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    idx = _idx if _idx is not None else _cargar_indice(dest)
    h = _huella(archivo)
    if h in idx:
        return None
    try:
        r = pdf.leer(archivo)
    except Exception:
        return None                          # no es un resumen conocido
    nombre = _nombre(r)
    destino, n = dest / nombre, 2
    while destino.exists():
        destino = dest / nombre.replace(".pdf", f"_{n}.pdf")
        n += 1
    shutil.copy2(archivo, destino)
    idx[h] = {"archivo": destino.name, "origen": archivo.name}
    if _idx is None:
        _guardar_indice(dest, idx)
    log(f"  + Importado: {archivo.name} → {destino.name}")
    return destino.name


def importar(descargas: str, reportes: str, dias: int = 120, log=print) -> list[str]:
    """Revisa la carpeta de Descargas (últimos `dias` días) e incorpora los resúmenes nuevos."""
    origen = Path(descargas).expanduser()
    dest = Path(reportes).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    if not origen.is_dir():
        log(f"  La carpeta de descargas {origen} no existe; no importo nada.")
        return []
    idx = _cargar_indice(dest)
    limite = time.time() - dias * 86400
    nuevos = []
    for p in sorted(origen.glob("*.pdf")):
        try:
            if p.stat().st_mtime >= limite and (n := incorporar(p, reportes, log, idx)):
                nuevos.append(n)
        except Exception:
            continue
    _guardar_indice(dest, idx)
    if not nuevos:
        log("  No hay resúmenes nuevos en Descargas.")
    return nuevos
