"""Análisis con IA, con proveedores intercambiables.

Cada proveedor es un módulo de esta carpeta con:
    ID, NOMBRE, DESCRIPCION
    SECRETO        nombre del secreto en el llavero (o None si no usa clave)
    MODELO         modelo por defecto
    USA_URL        True si se puede configurar la dirección del servidor
    disponible(opciones) -> (bool, str)
    generar(sistema, contenido, opciones, clave) -> str     # texto de la respuesta

Para sumar otro proveedor: copiá ia/_plantilla.py, completalo y agregalo a PROVEEDORES.

Lo que se envía es un resumen: saldos, posiciones, gastos por mes y los gastos más grandes,
sin números de cuenta, CBU ni CUIT (los números largos se borran antes de enviar).
"""
import json
import re

from . import anthropic_api, claude_code, ollama, openai_compatible

PROVEEDORES = {m.ID: m for m in (claude_code, anthropic_api, openai_compatible, ollama)}

SISTEMA = """Sos un analista de finanzas personales en Argentina. Recibís un JSON con la situación
actual de una persona (saldos, inversiones, gastos por mes, cotizaciones del dólar, tasas de
referencia). Montos en ARS salvo que se indique; "ars" es el equivalente en pesos al dólar MEP.
IMPORTANTE: los datos vienen de fuentes con fechas distintas. Los brokers con API son en vivo; los
bancos y billeteras salen de resúmenes PDF cuyo período está en "cobertura" y la fecha de cada
saldo en "al". Los gastos están agrupados por mes en "gastos_por_mes": un mes puede estar cubierto
solo parcialmente o por una sola entidad. Tenelo en cuenta y no saques conclusiones de meses
incompletos sin aclararlo. "Pago de tarjeta" es el pago del resumen de la tarjeta (no tenemos el
detalle de consumos). Las transferencias entre cuentas propias ya están excluidas de los totales.
"contra_inflacion" compara el patrimonio de la primera actualización con el de hoy contra la inflación del
período ("real_pct" es la variación real); incluye lo ahorrado y gastado, no es solo rendimiento.
"recurrentes" son los pagos que se repiten cada mes; "aumento" marca los que subieron respecto del mes anterior.
"objetivos" son las metas de ahorro de la persona y si llega a cumplirlas.

Analizá: liquidez ociosa en pesos frente a la inflación, exposición por moneda, concentración de la
cartera, gasto mensual frente a ingresos, categorías altas o llamativas, suscripciones, comisiones e
impuestos, y efectivo sin invertir en los brokers. Sé concreto y usá los números. No inventes datos
que no estén en el JSON. Esto es informativo, no asesoramiento financiero profesional.

Se lee en el celular de un vistazo: textos CORTOS, sin relleno, con números. Respetá los largos máximos.

Respondé SOLO con un JSON válido (sin markdown) con esta forma:
{"titular": "la conclusión principal, máximo 12 palabras",
 "salud": {"puntaje": 0, "etiqueta": "Muy bien | Bien | Regular | Atención"},
 "indicadores": [{"nombre": "Liquidez ociosa | Diversificación | Ahorro del mes | Exposición al dólar | ...",
                  "estado": "bien | regular | mal", "valor": "dato corto, ej. 38% o $2,8 M"}],
 "resumen": "máximo 2 oraciones",
 "observaciones": ["máximo 4, de hasta 15 palabras"],
 "alertas": [{"nivel": "alta|media|baja", "titulo": "hasta 8 palabras", "detalle": "hasta 25 palabras"}],
 "recomendaciones": [{"titulo": "hasta 8 palabras", "detalle": "hasta 25 palabras", "impacto": "alto|medio|bajo",
                      "ahorro_mensual_ars": 0}]}
"puntaje" va de 0 a 100 (salud financiera general). Entre 3 y 5 indicadores. "ahorro_mensual_ars" es lo
que ganaría o ahorraría por mes si sigue la recomendación (0 si no aplica)."""


def payload(resumen: dict, cotizaciones: dict, referencias: dict | None = None) -> str:
    r = json.loads(json.dumps(resumen, default=str))
    if isinstance(r.get("contra_inflacion"), dict):
        r["contra_inflacion"].pop("serie", None)        # el gráfico no le sirve a la IA
    for mes in r.get("gastos_por_mes", {}).values():
        for m in mes.get("top", []):
            m["descripcion"] = re.sub(r"\d{6,}", "…", m["descripcion"])  # sin CBU/CUIT/nros. de operación
    return json.dumps({"cotizaciones": cotizaciones, "referencias": referencias or {}, **r}, ensure_ascii=False)


def _a_json(texto: str) -> dict:
    try:
        return json.loads(texto[texto.index("{"): texto.rindex("}") + 1])
    except ValueError:
        return {"resumen": texto[:3000], "observaciones": [], "alertas": [], "recomendaciones": []}


a_json = _a_json


def consultar(sistema: str, contenido: str, cfg_analisis: dict, clave_de=None, log=print,
              web: bool = False, que: str = "Analizando") -> dict:
    """Consulta genérica al proveedor configurado. Devuelve {"texto", "proveedor", "modelo", "web"} o {"error"}."""
    pid = cfg_analisis.get("proveedor") or "claude_code"
    prov = PROVEEDORES.get(pid)
    if not prov:
        return {"error": f"Proveedor de IA desconocido: {pid}"}
    opciones = dict(cfg_analisis.get(pid, {}))
    opciones["modelo"] = opciones.get("modelo") or cfg_analisis.get("modelo") or prov.MODELO
    ok, detalle = prov.disponible(opciones)
    if not ok:
        return {"error": detalle}
    clave = None
    if prov.SECRETO:
        import os
        clave = (clave_de(prov.SECRETO) if clave_de else None) or os.environ.get(getattr(prov, "ENV", "") or "_")
        if not clave:
            return {"error": f"Falta la clave de {prov.NOMBRE} (guardala en Configuración → Análisis)"}
    usa_web = bool(web and getattr(prov, "WEB", False))
    log(f"  {que} con {prov.NOMBRE} ({opciones['modelo'] or 'modelo por defecto'}){' buscando noticias' if usa_web else ''}… puede tardar unos minutos")
    try:
        texto = prov.generar(sistema, contenido, opciones, clave, web=usa_web) if usa_web else prov.generar(sistema, contenido, opciones, clave)
    except Exception as e:
        from utils import mensaje_error
        return {"error": f"{prov.NOMBRE}: {mensaje_error(e, prov.NOMBRE)}"}
    finally:
        clave = None
    return {"texto": texto, "proveedor": prov.NOMBRE, "modelo": opciones["modelo"], "web": usa_web}


def analizar(resumen: dict, cotizaciones: dict, cfg_analisis: dict, clave_de=None,
             referencias: dict | None = None, log=print) -> dict:
    """Devuelve el análisis o {"error": motivo}. `clave_de(nombre)` lee un secreto del llavero."""
    pid = cfg_analisis.get("proveedor") or "claude_code"
    prov = PROVEEDORES.get(pid)
    if not prov:
        return {"error": f"Proveedor de IA desconocido: {pid}"}
    opciones = dict(cfg_analisis.get(pid, {}))
    opciones["modelo"] = opciones.get("modelo") or cfg_analisis.get("modelo") or prov.MODELO
    ok, detalle = prov.disponible(opciones)
    if not ok:
        return {"error": detalle}
    clave = None
    if prov.SECRETO:
        import os
        clave = (clave_de(prov.SECRETO) if clave_de else None) or os.environ.get(getattr(prov, "ENV", "") or "_")
        if not clave:
            return {"error": f"Falta la clave de {prov.NOMBRE} (guardala en Configuración → Análisis)"}
    log(f"  Analizando con {prov.NOMBRE} ({opciones['modelo'] or 'modelo por defecto'})… puede tardar un par de minutos")
    try:
        texto = prov.generar(SISTEMA, payload(resumen, cotizaciones, referencias), opciones, clave)
    except Exception as e:
        from utils import mensaje_error
        return {"error": f"{prov.NOMBRE}: {mensaje_error(e, prov.NOMBRE)}"}
    finally:
        clave = None
    a = _a_json(texto)
    a["proveedor"] = prov.NOMBRE
    a["modelo"] = opciones["modelo"]
    from . import normalizar
    return normalizar.general(a)


def probar(cfg_analisis: dict, clave_de=None) -> dict:
    """Prueba corta (sin datos personales) para el botón "Probar" de la configuración."""
    pid = cfg_analisis.get("proveedor") or "claude_code"
    prov = PROVEEDORES.get(pid)
    if not prov:
        return {"ok": False, "mensaje": "Proveedor desconocido"}
    opciones = dict(cfg_analisis.get(pid, {}))
    opciones["modelo"] = opciones.get("modelo") or prov.MODELO
    ok, detalle = prov.disponible(opciones)
    if not ok:
        return {"ok": False, "mensaje": detalle}
    clave = clave_de(prov.SECRETO) if (prov.SECRETO and clave_de) else None
    if prov.SECRETO and not clave:
        return {"ok": False, "mensaje": f"Guardá primero la clave de {prov.NOMBRE}"}
    try:
        t = prov.generar('Respondé solo con el JSON {"ok": true}.', "Prueba de conexión.", opciones, clave)
        return {"ok": True, "mensaje": f"{prov.NOMBRE} respondió correctamente ({opciones['modelo'] or 'modelo por defecto'})."
                if "ok" in t.lower() else f"{prov.NOMBRE} respondió, pero con un formato inesperado: {t[:120]}"}
    except Exception as e:
        return {"ok": False, "mensaje": str(e).splitlines()[0][:300]}
