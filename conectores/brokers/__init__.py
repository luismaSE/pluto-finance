"""Brokers con conexión en vivo (API).

Cada broker es un módulo con:
    ID, NOMBRE, DESCRIPCION
    CAMPOS = [{"id": "usuario", "etiqueta": "Usuario"}, {"id": "clave", "etiqueta": "Clave", "secreto": True}]
    obtener(credenciales: dict) -> (cuentas, movimientos, inversiones)

Los CAMPOS se piden en cada actualización (en la app o en la terminal) y no se guardan.
Para sumar uno: copiá _plantilla.py, completalo y agregalo a BROKERS.
"""
from . import iol

BROKERS = {m.ID: m for m in (iol,)}
