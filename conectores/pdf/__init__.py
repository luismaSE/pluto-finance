"""Lectura de resúmenes en PDF de bancos y billeteras.

Poné los PDF que descargás del home banking / app en la carpeta `reportes/`
(o pasalos con --reportes). Cada archivo se identifica solo por su contenido.

Cada lector es un módulo con ENTIDAD, TIPO ("banco" | "billetera" | "broker"), DOCUMENTO
(qué PDF lee y dónde se descarga), detectar(texto) y parsear(texto).
Para sumar un banco: copiá _plantilla.py, completalo y agregalo a PARSERS.
"""
from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader

from . import galicia_caja, galicia_fci, mercadopago

PARSERS = [galicia_caja, galicia_fci, mercadopago]


def entidades() -> list[dict]:
    """Entidades que se pueden leer por PDF, en orden, con los documentos que acepta cada una."""
    out = {}
    for p in PARSERS:
        e = out.setdefault(p.ENTIDAD, {"nombre": p.ENTIDAD, "tipo": getattr(p, "TIPO", "banco"), "metodo": "pdf", "documentos": []})
        if getattr(p, "DOCUMENTO", None):
            e["documentos"].append(p.DOCUMENTO)
    return list(out.values())


@dataclass
class Resultado:
    entidad: str
    descripcion: str                 # "Caja de ahorro en pesos 28/08–25/09"
    cuentas: list = field(default_factory=list)
    movimientos: list = field(default_factory=list)
    inversiones: list = field(default_factory=list)
    cobertura: dict | None = None    # {entidad, cuenta, desde, hasta}
    titular: str | None = None
    advertencias: list = field(default_factory=list)


def leer_texto(path: Path) -> str:
    r = PdfReader(str(path))
    return "\n".join(p.extract_text(extraction_mode="layout") or "" for p in r.pages)


def leer(path: Path) -> Resultado:
    texto = leer_texto(path)
    for p in PARSERS:
        if p.detectar(texto):
            return p.parsear(texto)
    raise ValueError("formato no reconocido (¿es un resumen de Galicia o Mercado Pago?)")


def archivos(rutas: list[str]) -> list[Path]:
    out = []
    for r in rutas:
        p = Path(r).expanduser()
        if p.is_dir():
            out += sorted(x for x in p.iterdir() if x.suffix.lower() == ".pdf")
        elif p.suffix.lower() == ".pdf" and p.exists():
            out.append(p)
    return out
