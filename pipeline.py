"""El proceso completo, compartido por la terminal (main.py) y la app de escritorio (escritorio/).

    importar Descargas -> leer PDFs -> brokers -> cotizaciones y tasas -> categorías -> resumen
    -> historial -> análisis con IA -> dashboard HTML -> (opcional) cifrar y publicar
"""
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import cotizaciones
import dashboard
import historial
import resumen
from categorias import categorizar
from modelo import Snapshot


ULTIMO_ANALISIS = Path("salida/ultimo_analisis.json")
ULTIMO_MERCADO = Path("salida/ultimo_mercado.json")
RESUMEN_MERCADO = Path("salida/resumen_mercado.json")   # lo que muestra Inicio en la app de escritorio


def demo_config() -> dict:
    """Configuración de ejemplo para --demo: límites y tarjetas ficticios."""
    import configuracion
    from datetime import timedelta
    cfg = configuracion.cargar()
    hoy = date.today()
    cfg["presupuestos"] = {"total": 1_200_000, "categorias": {"Supermercado": 350_000, "Delivery y restaurantes": 60_000, "Suscripciones": 30_000}}
    cfg["tarjetas"] = {
        "visa": {"nombre": "Visa", "cierre": (hoy + timedelta(days=9)).day, "vencimiento": (hoy + timedelta(days=2)).day},
        "master": {"nombre": "Mastercard", "cierre": (hoy + timedelta(days=16)).day, "vencimiento": (hoy + timedelta(days=12)).day},
    }
    cfg["categorias"] = {"reglas": {}}
    cfg["objetivos"] = {
        "viaje": {"nombre": "Viaje a Europa", "monto": 4000, "moneda": "USD", "fecha": (hoy + timedelta(days=240)).isoformat(), "ahorrado": 1500},
        "auto": {"nombre": "Cambiar el auto", "monto": 18_000_000, "moneda": "ARS", "fecha": (hoy + timedelta(days=420)).isoformat(), "ahorrado": 3_000_000},
        "notebook": {"nombre": "Notebook", "monto": 1_900_000, "moneda": "ARS", "fecha": (hoy + timedelta(days=60)).isoformat(), "ahorrado": 1_900_000},
    }
    return cfg   # local, nunca se sube al repo


def _ultimo_analisis(ruta=ULTIMO_ANALISIS) -> dict | None:
    import datos_locales
    return datos_locales.leer(ruta, None)


def _con_respaldo(nuevo: dict | None, ruta: Path, log) -> dict | None:
    """Guarda el análisis si salió bien; si no (no se pidió o falló), devuelve el último que salió bien."""
    import datos_locales
    if nuevo and not nuevo.get("error"):
        nuevo.setdefault("fecha", datetime.now().isoformat(timespec="minutes"))
        datos_locales.escribir(ruta, nuevo)
        log("  ✓ Análisis listo")
        return nuevo
    previo = _ultimo_analisis(ruta)
    if previo:
        previo["anterior"] = True
        if nuevo and nuevo.get("error"):
            previo["error_nuevo"] = nuevo["error"]
        log(f"  Se mantiene el análisis anterior ({previo.get('fecha', 'sin fecha')}).")
        return previo
    return nuevo


@dataclass
class Opciones:
    reportes: list = field(default_factory=lambda: ["reportes"])
    descargas: str | None = None          # carpeta de la que se importan resúmenes nuevos
    # brokers a consultar: {"iol": {"usuario": ..., "clave": ...}}. Si faltan datos y la
    # corrida es interactiva, se piden en la terminal. Nunca se guardan.
    brokers: dict = field(default_factory=dict)
    analisis: bool = True
    mercado: bool = False                 # análisis de mercado (solo lectura: nunca opera)
    ia: dict = field(default_factory=dict)          # sección [analisis] de la configuración
    celular: bool = False
    celular_password: str | None = None
    github_token: str | None = None
    referencias: dict = field(default_factory=dict)
    publicar: dict = field(default_factory=dict)
    interactivo: bool = True              # False en la app: nunca usa input()
    demo: bool = False
    config: dict | None = None            # configuración completa; si falta se lee config.toml


def _pedir_campos(b, cred: dict) -> dict:
    import getpass
    for c in b.CAMPOS:
        if not cred.get(c["id"]):
            pregunta = f"{b.NOMBRE} - {c['etiqueta']}: "
            cred[c["id"]] = getpass.getpass(pregunta) if c.get("secreto") else input(pregunta).strip()
    return cred


def _acepta_extra(b) -> bool:
    import inspect
    return "extra" in inspect.signature(b.obtener).parameters


def _cargar_brokers(s: Snapshot, o: Opciones, log, extra: dict | None = None):
    """`extra` (opcional) pide datos de mercado a los brokers que los ofrecen; quedan en extra["precios"]."""
    from conectores.brokers import BROKERS
    for bid, cred in list(o.brokers.items()):
        b = BROKERS.get(bid)
        if not b:
            log(f"\n✗ Broker desconocido: {bid}")
            continue
        log(f"\n=== {b.NOMBRE} ===")
        try:
            cred = dict(cred or {})
            if o.interactivo:
                cred = _pedir_campos(b, cred)
            faltan = [c["etiqueta"] for c in b.CAMPOS if not cred.get(c["id"])]
            if faltan:
                raise RuntimeError("faltan datos de acceso: " + ", ".join(faltan))
            if extra is not None and _acepta_extra(b):
                c, m, i = b.obtener(cred, extra=extra)
            else:
                c, m, i = b.obtener(cred)
            hoy = date.today().isoformat()
            for x in c + i:
                x.al = x.al or hoy
            s.cuentas += c
            s.movimientos += m
            s.inversiones += i
            s.estado_fuentes[b.NOMBRE] = {"ok": True, "detalle": f"API en vivo: {len(c)} saldos, {len(i)} posiciones"}
            log(f"  ✓ {len(c)} saldos, {len(i)} posiciones")
        except Exception as e:
            from utils import mensaje_error
            msg = mensaje_error(e, b.NOMBRE)
            log(f"  ✗ {msg}")
            s.estado_fuentes[b.NOMBRE] = {"ok": False, "detalle": msg}
        finally:
            cred = None
            o.brokers[bid] = None          # descarta las credenciales


def _cargar_pdfs(s: Snapshot, rutas, log) -> set:
    from conectores import pdf
    titulares, detalle = set(), {}
    archivos = pdf.archivos(rutas)
    log(f"\n=== Reportes PDF ({len(archivos)}) ===")
    if not archivos:
        log("  No encontré PDFs. Descargá los resúmenes (o configurá la carpeta de Descargas).")
    for f in archivos:
        try:
            r = pdf.leer(f)
        except Exception as e:
            log(f"  ✗ {f.name}: {e}")
            s.advertencias.append(f"No pude leer {f.name}: {e}")
            continue
        log(f"  ✓ {f.name}: {r.entidad} · {r.descripcion} · {len(r.movimientos)} movimientos")
        s.cuentas += r.cuentas
        s.movimientos += r.movimientos
        s.inversiones += r.inversiones
        s.advertencias += r.advertencias
        if r.cobertura:
            s.cobertura.append(r.cobertura)
        if r.titular:
            titulares.add(r.titular)
        detalle.setdefault(r.entidad, []).append(r.descripcion)
    for ent, ds in detalle.items():
        s.estado_fuentes[ent] = {"ok": True, "detalle": "PDF: " + "; ".join(ds)}
    return titulares


def ejecutar(o: Opciones, log=print) -> dict:
    """Corre todo y devuelve {"dashboard": ruta, "datos": dict, "publicado": bool}."""
    import configuracion
    cfg = o.config or (demo_config() if o.demo else configuracion.cargar())
    titulares = set()
    cfg_mercado = cfg.get("mercado") or {}
    extra_mercado = {"mercado": True, "seguimiento": list(cfg_mercado.get("seguimiento") or [])} if o.mercado else None
    precios = {}
    if o.demo:
        from demo import snapshot_demo
        s = snapshot_demo()
        from demo import inflacion_demo
        refs = {"tna_plazo_fijo": 0.30, "tna_fuente": "demo", "inflacion_mensual": 0.025, "inflacion_mes": "demo",
                "inflacion_serie": inflacion_demo()}
    else:
        if o.descargas:
            from importar import importar
            log("=== Importar desde Descargas ===")
            importar(o.descargas, o.reportes[0], log=log)
        s = Snapshot()
        log("=== Cotizaciones ===")
        s.cotizaciones = cotizaciones.obtener(pedir_mep=o.interactivo)
        refs = cotizaciones.referencias(o.referencias)
        log(f"  MEP: {s.cotizaciones.get('mep', {}).get('venta', 'sin dato')}"
            + (f" · TNA plazo fijo {refs['tna_plazo_fijo']*100:.1f}%" if refs.get("tna_plazo_fijo") else ""))
        titulares = _cargar_pdfs(s, o.reportes, log)
        if o.brokers:
            _cargar_brokers(s, o, log, extra_mercado)

    for m in s.movimientos:
        m.categoria = m.categoria or categorizar(m.descripcion, titulares, cfg["categorias"].get("reglas"))
    if not s.cotizaciones.get("mep"):
        s.advertencias.append("Sin cotización MEP: los saldos en USD no se suman al total en pesos.")

    r = resumen.calcular(s)
    # Tarjetas, límites de gasto, metas y avisos (también le llegan al análisis con IA)
    import avisos
    import presupuestos
    import tarjetas
    r["tarjetas"] = tarjetas.calcular(cfg["tarjetas"], date.today(), s.movimientos)
    r["presupuestos"] = presupuestos.evaluar(cfg["presupuestos"], r["gastos_por_mes"])
    r["metas"] = cfg["metas"]
    import recurrentes
    r["recurrentes"] = recurrentes.detectar(s.movimientos, r.get("categorias_excluidas") or (), r.get("tipo_cambio_mep"))
    import objetivos
    r["objetivos"] = objetivos.evaluar(cfg.get("objetivos"), r["gastos_por_mes"], r.get("tipo_cambio_mep"))
    r["avisos"] = avisos.generar(r, r["tarjetas"], r["presupuestos"]) + objetivos.avisos(r["objetivos"]) + recurrentes.avisos(r["recurrentes"])
    if o.demo:
        from demo import historial_demo
        hist = historial_demo()
    else:
        hist = historial.agregar(r, s.estado_fuentes)
    # ¿Le ganás a la inflación? (también le llega al análisis con IA)
    import rendimiento
    r["contra_inflacion"] = rendimiento.contra_inflacion(historial.por_dia(hist), refs.get("inflacion_serie"))

    if not o.demo:
        nuevo = None
        if o.analisis:
            import ia
            log("\n=== Análisis con IA ===")
            nuevo = ia.analizar(r, s.cotizaciones, o.ia or cfg["analisis"], configuracion.leer_secreto, refs, log)
            if nuevo.get("error"):
                log(f"  ✗ {nuevo['error']}")
        s.analisis = _con_respaldo(nuevo, ULTIMO_ANALISIS, log)

    # Análisis de mercado: SOLO LECTURA. Analiza y recomienda; Pluto nunca opera.
    mercado_datos = None
    if o.demo:
        import demo
        import mercado
        precios = demo.precios_demo()
        mercado_datos = mercado.para_dashboard(demo.analisis_mercado_demo(), precios, demo.registro_demo(precios))
    elif o.mercado or _ultimo_analisis(ULTIMO_MERCADO):
        import datos_locales
        import mercado
        precios = (extra_mercado or {}).get("precios") or {}
        nuevo_m = None
        if o.mercado:
            log("\n=== Análisis de mercado ===")
            if not precios:
                log("  Sin precios de IOL: el análisis usa solo tu cartera" + (" (activá IOL para sumar precios e historia)." if not o.brokers else "."))
            nuevo_m = mercado.analizar(r, precios, cfg_mercado, o.ia or cfg["analisis"], s.cotizaciones, refs,
                                       configuracion.leer_secreto, log)
            if nuevo_m.get("error"):
                log(f"  ✗ {nuevo_m['error']}")
            else:
                mercado.registrar(nuevo_m, precios)
        analisis_m = _con_respaldo(nuevo_m, ULTIMO_MERCADO, log) if o.mercado else _ultimo_analisis(ULTIMO_MERCADO)
        if analisis_m and not o.mercado:
            analisis_m["anterior"] = True
        mercado_datos = mercado.para_dashboard(analisis_m, precios, datos_locales.leer(mercado.REGISTRO, []) or [])
        datos_locales.escribir(RESUMEN_MERCADO, mercado.resumen_corto(mercado_datos))

    import fuentes
    datos = {"snapshot": s.to_dict(), "resumen": r, "demo": o.demo, "hoy": date.today().isoformat(),
             "referencias": refs, "historial": historial.por_dia(hist), "entidades": fuentes.nombres(),
             "mercado": mercado_datos}
    ruta = dashboard.generar(datos, abrir=False)
    log(f"\nDashboard: {Path(ruta).resolve()}")
    if not o.demo:
        import datos_locales
        borrados = datos_locales.limpiar_dashboards(str(Path(ruta).parent), cfg["privacidad"].get("conservar_dashboards", 5))
        if borrados:
            log(f"  Se borraron {borrados} dashboards viejos (se conservan los últimos {cfg['privacidad'].get('conservar_dashboards', 5)}).")

    publicado = False
    if o.celular:
        import cifrado
        import publicar
        log("\n=== Celular ===")
        try:
            pw = o.celular_password or (cifrado.pedir_password() if o.interactivo else None)
            if not pw:
                raise RuntimeError("Falta la contraseña del celular (guardala en Configuración)")
            if len(pw) < cifrado.LARGO_MINIMO:
                raise RuntimeError(f"La contraseña del celular debe tener al menos {cifrado.LARGO_MINIMO} caracteres")
            publicar.publicar(cifrado.cifrar(datos, pw), o.publicar, o.github_token, log, preguntar=o.interactivo)
            publicado = True
        except Exception as e:
            from utils import mensaje_error
            destino = {"github": "GitHub", "drive": "Google Drive"}.get(o.publicar.get("destino"), "el destino")
            log(f"  ✗ No pude publicar: {mensaje_error(e, destino)}")
        finally:
            o.celular_password = None
            o.github_token = None
    return {"dashboard": str(ruta), "datos": datos, "publicado": publicado}
