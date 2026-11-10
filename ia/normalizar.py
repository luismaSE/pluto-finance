"""Revisa la respuesta de la IA antes de mostrarla.

Los modelos a veces devuelven números fuera de rango, listas larguísimas, valores que no existen o
tipos equivocados (un número como texto, una lista como texto). Acá se corrige lo que se puede y
se descarta lo que no tiene sentido, para que el dashboard nunca dibuje algo roto o engañoso.
"""
import re


def texto(v, maximo: int = 400) -> str:
    """Texto limpio de una línea, cortado en `maximo` caracteres."""
    if v is None or isinstance(v, (dict, list)):
        return ""
    t = re.sub(r"\s+", " ", str(v)).strip()
    return t if len(t) <= maximo else t[: maximo - 1].rstrip() + "…"


def numero(v, minimo=None, maximo=None, defecto=None):
    """Número dentro de [minimo, maximo]. Acepta "1.500.000", "$ 2,5", "38%"."""
    if isinstance(v, bool):
        return defecto
    if isinstance(v, str):
        s = re.sub(r"[^\d,.\-]", "", v)
        if s.count(",") == 1 and s.count(".") != 1:      # formato argentino: 1.500.000,50
            s = s.replace(".", "").replace(",", ".")
        elif s.count(".") > 1:
            s = s.replace(".", "")
        s = s.replace(",", "")
        try:
            v = float(s)
        except ValueError:
            return defecto
    if not isinstance(v, (int, float)) or v != v:         # NaN
        return defecto
    if minimo is not None:
        v = max(minimo, v)
    if maximo is not None:
        v = min(maximo, v)
    return int(v) if float(v).is_integer() else v


def opcion(v, validas, defecto=None):
    """Uno de los valores válidos (sin importar mayúsculas ni acentos), o `defecto`."""
    t = _sin_acentos(texto(v, 40)).lower()
    for x in validas:
        if t == _sin_acentos(x).lower():
            return x
    return defecto


def lista(v, maximo: int = 30) -> list:
    """Lista de hasta `maximo` elementos (un texto suelto cuenta como lista de uno)."""
    if isinstance(v, str):
        v = [v] if v.strip() else []
    return list(v)[:maximo] if isinstance(v, (list, tuple)) else []


def _sin_acentos(t: str) -> str:
    return t.translate(str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU"))


NIVELES = ("baja", "media", "alta")


def general(a: dict) -> dict:
    """Análisis general (pestaña Análisis)."""
    out = {k: a[k] for k in ("proveedor", "modelo", "fecha") if k in a}
    out["resumen"] = texto(a.get("resumen"), 600)
    if a.get("titular"):
        out["titular"] = texto(a["titular"], 120)
    s = a.get("salud") if isinstance(a.get("salud"), dict) else {}
    p = numero(s.get("puntaje"), 0, 100)
    if p is not None:
        out["salud"] = {"puntaje": round(p), "etiqueta": texto(s.get("etiqueta"), 20)}
    out["indicadores"] = [{"nombre": texto(i.get("nombre"), 40), "estado": opcion(i.get("estado"), ("bien", "regular", "mal"), "regular"),
                           "valor": texto(i.get("valor"), 24)}
                          for i in lista(a.get("indicadores")) if isinstance(i, dict) and texto(i.get("nombre"))][:6]
    out["observaciones"] = [texto(o, 160) for o in lista(a.get("observaciones")) if texto(o)][:6]
    out["alertas"] = [{"nivel": opcion(x.get("nivel"), NIVELES, "media"), "titulo": texto(x.get("titulo"), 90),
                       "detalle": texto(x.get("detalle"), 300)}
                      for x in lista(a.get("alertas")) if isinstance(x, dict) and texto(x.get("titulo"))][:6]
    out["recomendaciones"] = [{"titulo": texto(x.get("titulo"), 90), "detalle": texto(x.get("detalle"), 300),
                               "impacto": opcion(x.get("impacto"), ("alto", "medio", "bajo"), "medio"),
                               "ahorro_mensual_ars": numero(x.get("ahorro_mensual_ars"), 0, defecto=0)}
                              for x in lista(a.get("recomendaciones")) if isinstance(x, dict) and texto(x.get("titulo"))][:6]
    return out


ACCIONES = ("aumentar", "reducir", "mantener", "comprar", "vender", "cambiar")
IMPACTOS = ("positivo", "negativo", "neutral", "incierto")
EFECTOS = ("positivo", "negativo", "mixto")


def mercado(a: dict) -> dict:
    """Análisis de mercado (pestaña Mercado)."""
    out = {k: a[k] for k in ("proveedor", "modelo", "fecha", "con_noticias") if k in a}
    out["resumen"] = texto(a.get("resumen"), 700)
    if a.get("titular"):
        out["titular"] = texto(a["titular"], 120)
    out["puntos_clave"] = [texto(x, 120) for x in lista(a.get("puntos_clave")) if texto(x)][:3]
    t = a.get("termometro") if isinstance(a.get("termometro"), dict) else {}
    termo = {k: round(n) for k in ("riesgo_cartera", "riesgo_perfil", "diversificacion")
             if (n := numero(t.get(k), 1, 5)) is not None}
    if (s := opcion(t.get("sentimiento"), ("positivo", "neutral", "negativo"))):
        termo["sentimiento"] = s
    if termo:
        out["termometro"] = termo
    filas = [{"clase": texto(f.get("clase"), 50), "actual_pct": numero(f.get("actual_pct"), 0, 100, 0),
              "objetivo_pct": numero(f.get("objetivo_pct"), 0, 100, 0), "comentario": texto(f.get("comentario"), 140)}
             for f in lista(a.get("cartera_objetivo")) if isinstance(f, dict) and texto(f.get("clase"))][:8]
    out["cartera_objetivo"] = filas if sum(f["objetivo_pct"] for f in filas) > 0 else []
    recos = []
    for x in lista(a.get("recomendaciones")):
        if len(recos) == 4:
            break
        accion = opcion(x.get("accion"), ACCIONES) if isinstance(x, dict) else None
        activo = texto(x.get("activo"), 40) if isinstance(x, dict) else ""
        if not accion or not activo:
            continue                                      # una recomendación sin acción o sin activo no se puede seguir
        por = texto(x.get("por"), 40) if accion == "cambiar" else ""
        recos.append({"accion": accion, "activo": activo, "por": por, "titulo": texto(x.get("titulo"), 80),
                      "monto_ars": numero(x.get("monto_ars"), 0, defecto=0), "motivo": texto(x.get("motivo"), 300),
                      "riesgos": texto(x.get("riesgos"), 240),
                      "horizonte": opcion(x.get("horizonte"), ("corto", "mediano", "largo"), ""),
                      "confianza": opcion(x.get("confianza"), NIVELES, "baja")})
    out["recomendaciones"] = recos
    out["noticias"] = [{"titulo": texto(n.get("titulo"), 160), "fuente": texto(n.get("fuente"), 60),
                        "fecha": texto(n.get("fecha"), 10) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto(n.get("fecha"), 10)) else "",
                        "activos": [texto(s, 20).upper() for s in lista(n.get("activos"), 6) if texto(s)],
                        "impacto": opcion(n.get("impacto"), IMPACTOS, "incierto"), "que_significa": texto(n.get("que_significa"), 240)}
                       for n in lista(a.get("noticias")) if isinstance(n, dict) and texto(n.get("titulo"))][:5]
    escen = []
    for e in lista(a.get("escenarios")):
        if len(escen) == 3:
            break
        if not isinstance(e, dict) or not texto(e.get("escenario")):
            continue
        efecto = opcion(e.get("efecto"), EFECTOS)
        detalle = texto(e.get("detalle"), 240) or ("" if efecto else texto(e.get("efecto"), 240))   # formato anterior
        escen.append({"escenario": texto(e.get("escenario"), 120), "probabilidad": opcion(e.get("probabilidad"), NIVELES, "media"),
                      "efecto": efecto or "mixto", "detalle": detalle, "que_considerar": texto(e.get("que_considerar"), 240)})
    out["escenarios"] = escen
    return out
