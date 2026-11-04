"""Plantilla para sumar un banco, billetera o broker que entrega resúmenes en PDF.

1. Copiá este archivo como conectores/pdf/mi_banco_caja.py.
2. Mirá el texto de tu PDF:  python -c "from conectores.pdf import leer_texto; print(leer_texto('resumen.pdf'))"
3. Completá detectar() con algo que solo aparezca en ese resumen y parsear() con expresiones
   regulares para las líneas de movimientos (fecha, descripción, monto, saldo).
4. Agregalo a PARSERS en conectores/pdf/__init__.py.
Ejemplos completos: galicia_caja.py (caja de ahorro), galicia_fci.py (fondos), mercadopago.py.
"""
import re

from modelo import Cuenta, Movimiento   # noqa: F401
from .comun import ddmmyy, monto, verificar_saldos   # noqa: F401

ENTIDAD = "Mi banco"
TIPO = "banco"                      # "banco" | "billetera" | "broker"
DOCUMENTO = "Resumen de caja de ahorro: Cuentas → Resúmenes"


def detectar(texto: str) -> bool:
    return "MI BANCO" in texto and "Resumen de cuenta" in texto


def parsear(texto: str):
    from . import Resultado
    res = Resultado(ENTIDAD, "Caja de ahorro")
    # res.cuentas.append(Cuenta(ENTIDAD, "Caja de ahorro en pesos", "ARS", saldo_final, fecha_hasta))
    # res.movimientos.append(Movimiento(fecha_iso, ENTIDAD, descripcion, monto_con_signo, "ARS"))
    # res.cobertura = {"entidad": ENTIDAD, "cuenta": "Caja de ahorro en pesos", "desde": ..., "hasta": ...}
    return res
