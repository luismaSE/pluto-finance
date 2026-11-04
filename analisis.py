"""Envía un resumen (sin números de cuenta ni datos personales) a Claude Code
(`claude -p`) y recibe observaciones, alertas y recomendaciones en JSON."""
import json
import re
import shutil
import subprocess

PROMPT = """Sos un analista de finanzas personales en Argentina. Por stdin recibís un JSON con mi
situación actual (saldos, inversiones, gastos del mes, cotizaciones del dólar). Montos en ARS salvo
que se indique; "ars" es el equivalente en pesos al dólar MEP.
IMPORTANTE: los datos vienen de fuentes con fechas distintas. IOL es en vivo; Galicia y Mercado
Pago salen de resúmenes PDF cuyo período está en "cobertura" y la fecha de cada saldo en "al".
Los gastos están agrupados por mes en "gastos_por_mes": un mes puede estar cubierto solo
parcialmente o por una sola entidad. Tenelo en cuenta y no saques conclusiones de meses incompletos
sin aclararlo. "Pago de tarjeta" es el pago del resumen de la tarjeta (no tenemos el detalle de
consumos). Las transferencias entre cuentas propias ya están excluidas de los totales.

Analizá: liquidez ociosa en pesos frente a la inflación, exposición por moneda, concentración de la
cartera, gasto mensual frente a ingresos, categorías
altas o llamativas, suscripciones, comisiones e impuestos, y efectivo sin invertir en el broker.
Sé concreto y usá los números. No inventes datos que no estén en el JSON. Esto es informativo,
no asesoramiento financiero profesional.

Respondé SOLO con un JSON válido (sin markdown) con esta forma:
{"resumen": "2-3 oraciones",
 "observaciones": ["..."],
 "alertas": [{"nivel": "alta|media|baja", "titulo": "...", "detalle": "..."}],
 "recomendaciones": [{"titulo": "...", "detalle": "...", "impacto": "alto|medio|bajo"}]}"""


def _payload(resumen: dict, cotizaciones: dict) -> dict:
    r = json.loads(json.dumps(resumen, default=str))
    for mes in r.get("gastos_por_mes", {}).values():
        for m in mes.get("top", []):
            m["descripcion"] = re.sub(r"\d{6,}", "…", m["descripcion"])  # sin CBU/CUIT/nros. de operación
    return {"cotizaciones": cotizaciones, **r}


def _error(msg):
    print("  ✗ Análisis de Claude:", msg)
    return {"error": msg}


def analizar(resumen: dict, cotizaciones: dict, modelo: str | None = None) -> dict:
    """Devuelve el análisis, o {"error": motivo} si no se pudo hacer."""
    exe = shutil.which("claude")
    if not exe:
        return _error("no encontré el comando `claude`. Instalá Claude Code y verificá que `claude --version` funcione en esta terminal.")
    cmd = [exe, "-p", PROMPT, "--output-format", "json"]
    if modelo:
        cmd += ["--model", modelo]
    print("Analizando con Claude... (puede tardar un par de minutos)")
    try:
        p = subprocess.run(cmd, input=json.dumps(_payload(resumen, cotizaciones), ensure_ascii=False),
                           capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return _error("Claude tardó más de 10 minutos.")
    except OSError as e:
        return _error(f"no pude ejecutar `claude`: {e}")

    try:
        salida = json.loads(p.stdout)
    except ValueError:
        detalle = (p.stderr or p.stdout).strip()[:400] or f"código de salida {p.returncode}"
        return _error(f"respuesta inesperada de Claude Code: {detalle}")
    texto = salida.get("result") or ""
    if p.returncode != 0 or salida.get("is_error"):
        msg = texto or (p.stderr or "").strip()[:400] or f"código de salida {p.returncode}"
        if "login" in msg.lower() or "api key" in msg.lower() or "auth" in msg.lower():
            msg += "  →  Corré `claude` una vez en la terminal e iniciá sesión."
        return _error(msg)
    try:
        return json.loads(texto[texto.index("{"): texto.rindex("}") + 1])
    except ValueError:
        print("  Claude respondió en texto libre; lo muestro tal cual.")
        return {"resumen": texto[:3000], "observaciones": [], "alertas": [], "recomendaciones": []}


if __name__ == "__main__":
    # Prueba rápida: python analisis.py
    r = analizar({"patrimonio_ars": 1000000, "gastos_por_mes": {}}, {"mep": {"venta": 1480}})
    print(json.dumps(r, ensure_ascii=False, indent=1)[:1500])
