"""Historial chico de cada corrida (solo totales, sin movimientos ni descripciones).
Se guarda en salida/historial.json, que nunca se sube al repo."""
import json
from datetime import datetime
from pathlib import Path

ARCHIVO = Path("salida/historial.json")


def cargar() -> list:
    try:
        return json.loads(ARCHIVO.read_text())
    except Exception:
        return []


def agregar(resumen: dict, estado_fuentes: dict) -> list:
    h = cargar()
    h.append({
        "fecha": datetime.now().isoformat(timespec="minutes"),
        "patrimonio_ars": resumen.get("patrimonio_ars"),
        "patrimonio_usd": resumen.get("patrimonio_usd"),
        "liquidez_ars": resumen.get("liquidez_ars"),
        "inversiones_ars": resumen.get("inversiones_ars"),
        "tipo_cambio_mep": resumen.get("tipo_cambio_mep"),
        "por_entidad": resumen.get("por_entidad"),
        "fuentes_ok": [k for k, v in estado_fuentes.items() if v.get("ok")],
        "fuentes_error": {k: v.get("detalle") for k, v in estado_fuentes.items() if not v.get("ok")},
        "avisos": resumen.get("avisos", []),
    })
    h = h[-500:]
    ARCHIVO.parent.mkdir(exist_ok=True)
    ARCHIVO.write_text(json.dumps(h, indent=1, ensure_ascii=False))
    return h


def por_dia(h: list) -> list:
    """Un punto por día (la última corrida de cada día), para graficar la evolución."""
    dias = {}
    for x in h:
        if x.get("patrimonio_ars"):
            dias[x["fecha"][:10]] = x
    return [dias[k] for k in sorted(dias)]
