"""Importa resúmenes nuevos desde la carpeta de Descargas a reportes/.

Reconoce cada PDF por su contenido (no por el nombre). Lleva un índice con la huella
SHA-256 de cada archivo para no importar dos veces el mismo resumen.
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


def _indice(dest: Path) -> dict:
    f = dest / INDICE
    idx = json.loads(f.read_text()) if f.exists() else {}
    # sumar al índice los PDF que ya estaban en reportes/
    for p in dest.glob("*.pdf"):
        if p.name not in {v.get("archivo") for v in idx.values()}:
            idx[_huella(p)] = {"archivo": p.name}
    return idx


def importar(descargas: str, reportes: str, dias: int = 120, log=print) -> list[str]:
    origen = Path(descargas).expanduser()
    dest = Path(reportes).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    if not origen.is_dir():
        log(f"  La carpeta de descargas {origen} no existe; no importo nada.")
        return []
    idx = _indice(dest)
    limite = time.time() - dias * 86400
    nuevos = []
    for p in sorted(origen.glob("*.pdf")):
        try:
            if p.stat().st_mtime < limite:
                continue
            h = _huella(p)
            if h in idx:
                continue
            r = pdf.leer(p)                     # si no es un resumen conocido, tira error y se ignora
        except Exception:
            continue
        cob = r.cobertura or {}
        sufijo = cob.get("hasta") or (r.inversiones[0].al if r.inversiones else None) or time.strftime("%Y-%m-%d")
        base = f"{r.entidad}_{(cob.get('cuenta') or r.descripcion.split(' al ')[0])}_{sufijo}"
        nombre = "".join(c if c.isalnum() or c in "-_" else "_" for c in base).strip("_") + ".pdf"
        destino = dest / nombre
        n = 2
        while destino.exists():
            destino = dest / nombre.replace(".pdf", f"_{n}.pdf")
            n += 1
        shutil.copy2(p, destino)
        idx[h] = {"archivo": destino.name, "origen": p.name}
        nuevos.append(destino.name)
        log(f"  + Importado: {p.name} → {destino.name}")
    (dest / INDICE).write_text(json.dumps(idx, indent=1, ensure_ascii=False))
    if not nuevos:
        log("  No hay resúmenes nuevos en Descargas.")
    return nuevos
