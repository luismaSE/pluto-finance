"""Muestra el texto de un resumen PDF tal como lo leen los lectores de Pluto, con la opción de
anonimizarlo para compartirlo (por ejemplo, para pedir que se agregue un banco nuevo).

    python herramientas/texto_pdf.py resumen.pdf               # texto completo
    python herramientas/texto_pdf.py resumen.pdf --anonimizar  # sin datos personales

--anonimizar reemplaza todas las cifras por otras al azar (mantiene el formato: puntos, comas,
cantidad de dígitos y fechas válidas) y los nombres propios en mayúsculas o con mayúscula inicial
que no sean palabras comunes de un resumen. Revisá el resultado antes de compartirlo.
"""
import argparse
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Palabras que aparecen en cualquier resumen y conviene conservar para entender el formato
COMUNES = set("""
resumen cuenta caja ahorro pesos dolares dólares saldo saldos fecha descripcion descripción origen credito crédito debito
débito total movimientos movimiento periodo período inicial final entradas salidas detalle transferencia transferencias
recibida enviada pago pagos tarjeta visa master mastercard american express rendimiento rendimientos interes interés
capitalizado haberes acreditamiento debin recurrente servicio proveedores varios operacion operación cbu cvu cuit cuil
numero número tipo de del la el los las en por con para al y a o un una mes meses enero febrero marzo abril mayo junio
julio agosto septiembre setiembre octubre noviembre diciembre fondo fondos clase cuotas cuota valor valorizado tenencia
tenencias posicion posición comitente banco página pagina hoja usd ars ingreso dinero qr compra compras impuesto iva
comision comisión cierre vencimiento minimo mínimo consumos consumo limite límite disponible fima premium plus
""".split())


def anonimizar(texto: str, semilla: int = 0) -> str:
    rnd = random.Random(semilla)

    def cifras(m):
        s = m.group(0)
        if re.fullmatch(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", s):          # fechas: día y mes válidos
            sep = "/" if "/" in s else "-"
            partes = s.split(sep)
            return sep.join([f"{rnd.randint(1, 28):02d}", f"{rnd.randint(1, 12):02d}", partes[2]])
        return re.sub(r"\d", lambda _: str(rnd.randint(0, 9)), s)

    texto = re.sub(r"\d[\d./,-]*\d|\d", cifras, texto)

    def nombre(m):
        w = m.group(0)
        if w.lower() in COMUNES or len(w) <= 2:
            return w
        return "X" * len(w) if w.isupper() else "X" + "x" * (len(w) - 1)

    return re.sub(r"\b[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+\b", nombre, texto)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--anonimizar", action="store_true")
    a = ap.parse_args()
    from conectores.pdf import leer_texto
    t = leer_texto(Path(a.pdf))
    print(anonimizar(t) if a.anonimizar else t)


if __name__ == "__main__":
    main()
