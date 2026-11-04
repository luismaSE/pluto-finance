"""Catálogo de todas las fuentes de datos: bancos y billeteras (PDF) y brokers (API).
Lo usan la app (para listar fuentes y pedir credenciales) y el dashboard (colores fijos por entidad)."""
from conectores import pdf
from conectores.brokers import BROKERS


def catalogo(cfg: dict | None = None) -> list[dict]:
    brokers_cfg = (cfg or {}).get("brokers", {})
    lista = pdf.entidades()
    nombres = {e["nombre"] for e in lista}
    for b in BROKERS.values():
        item = {"nombre": b.NOMBRE, "tipo": "broker", "metodo": "api", "id": b.ID, "descripcion": b.DESCRIPCION,
                "campos": b.CAMPOS, "activo": bool(brokers_cfg.get(b.ID, {}).get("activo"))}
        if b.NOMBRE in nombres:                       # misma entidad por PDF y por API
            next(e for e in lista if e["nombre"] == b.NOMBRE).update(item)
        else:
            lista.append(item)
    return lista


def nombres() -> list[str]:
    """Orden estable de entidades: define el color de cada una en el dashboard."""
    return [e["nombre"] for e in catalogo()]
