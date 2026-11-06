"""Plantilla para sumar un proveedor de IA.

1. Copiá este archivo como ia/mi_proveedor.py y completalo.
2. Importalo en ia/__init__.py y agregalo a PROVEEDORES.
3. Si usa clave, agregá SECRETO a configuracion.SECRETOS (aparece solo en la app para guardarla).
"""
ID = "mi_proveedor"
NOMBRE = "Mi proveedor"
DESCRIPCION = "Una línea que se muestra en la configuración."
SECRETO = None          # ej. "ia_mi_proveedor" si necesita clave (se guarda en el llavero)
ENV = ""                # variable de entorno alternativa para la clave (opcional)
MODELO = ""             # modelo por defecto
USA_URL = False         # True si el usuario puede cambiar la dirección del servidor
WEB = False             # True si puede buscar en la web (noticias para el análisis de mercado)


def disponible(opciones: dict) -> tuple[bool, str]:
    """Chequeo rápido antes de usarlo (librería instalada, servidor encendido, etc.)."""
    return True, "ok"


def generar(sistema: str, contenido: str, opciones: dict, clave: str | None, web: bool = False) -> str:
    """Manda `sistema` (instrucciones) y `contenido` (JSON con los datos) y devuelve el texto de la respuesta.
    `opciones` trae "modelo" y, si USA_URL, "url". Lanzá RuntimeError con un mensaje claro si falla."""
    raise NotImplementedError
