"""Genera el dashboard: un único HTML autocontenido (sin internet, sin servidor)."""
import json
import webbrowser
from datetime import datetime
from pathlib import Path

PLANTILLA = Path(__file__).parent / "plantillas" / "dashboard.html"


def generar(datos: dict, destino: Path | None = None, abrir=True) -> Path:
    html = PLANTILLA.read_text(encoding="utf-8")
    js = json.dumps(datos, ensure_ascii=False, default=str).replace("</", "<\\/")
    html = html.replace("/*__DATOS__*/null", js)
    if destino is None:
        Path("salida").mkdir(exist_ok=True)
        destino = Path("salida") / f"dashboard_{datetime.now():%Y-%m-%d_%H%M}.html"
    destino.write_text(html, encoding="utf-8")
    if abrir:
        webbrowser.open(destino.resolve().as_uri())
    return destino
