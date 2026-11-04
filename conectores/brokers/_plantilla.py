"""Plantilla para sumar un broker con API (Balanz, Cocos, PPI, Bull Market, etc.).

1. Copiá este archivo como conectores/brokers/mi_broker.py y completalo.
2. Agregalo a BROKERS en conectores/brokers/__init__.py.
3. Activalo en la app: Configuración → Fuentes de datos.
Si el broker no tiene API pero da resúmenes en PDF, mejor sumalo como lector de PDF
(ver conectores/pdf/_plantilla.py).
"""
from modelo import Cuenta, Inversion   # noqa: F401  (tipos que tenés que devolver)

ID = "mi_broker"
NOMBRE = "Mi broker"
DESCRIPCION = "Una línea que se muestra en la configuración."
CAMPOS = [
    {"id": "usuario", "etiqueta": "Usuario"},
    {"id": "clave", "etiqueta": "Clave", "secreto": True},
]


def obtener(credenciales: dict):
    """Iniciá sesión con `credenciales`, traé saldos y posiciones, y descartá el token al terminar.
    Devolvé (cuentas: list[Cuenta], movimientos: list, inversiones: list[Inversion])."""
    raise NotImplementedError
