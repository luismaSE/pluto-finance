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
    return cfg   # local, nunca se sube al repo


def _guardar_analisis(a: dict):
    ULTIMO_ANALISIS.parent.mkdir(exist_ok=True)
    ULTIMO_ANALISIS.write_text(json.dumps(a, ensure_ascii=False, indent=1), encoding="utf-8")


def _ultimo_analisis() -> dict | None:
    try:
        return json.loads(ULTIMO_ANALISIS.read_text(encoding="utf-8"))
    except Exception:
        return None


@dataclass
class Opciones:
    reportes: list = field(default_factory=lambda: ["reportes"])
    descargas: str | None = None          # carpeta de la que se importan resúmenes nuevos
    # brokers a consultar: {"iol": {"usuario": ..., "clave": ...}}. Si faltan datos y la
    # corrida es interactiva, se piden en la terminal. Nunca se guardan.
    brokers: dict = field(default_factory=dict)
    analisis: bool = True
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


def _cargar_brokers(s: Snapshot, o: Opciones, log):
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
            log(f"  ✗ Error en {b.NOMBRE}: {e}")
            s.estado_fuentes[b.NOMBRE] = {"ok": False, "detalle": str(e)[:200]}
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
    import configuracion
    cfg = o.config or (demo_config() if o.demo else configuracion.cargar())
    """Corre todo y devuelve {"dashboard": ruta, "datos": dict, "publicado": bool}."""
    titulares = set()
    if o.demo:
        from demo import snapshot_demo
        s = snapshot_demo()
        refs = {"tna_plazo_fijo": 0.30, "tna_fuente": "demo", "inflacion_mensual": 0.025, "inflacion_mes": "demo"}
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
            _cargar_brokers(s, o, log)

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
    r["avisos"] = avisos.generar(r, r["tarjetas"], r["presupuestos"])
    hist = historial.cargar() if o.demo else historial.agregar(r, s.estado_fuentes)

    if not o.demo:
        nuevo = None
        if o.analisis:
            import configuracion
            import ia
            log("\n=== Análisis con IA ===")
            nuevo = ia.analizar(r, s.cotizaciones, o.ia or configuracion.cargar()["analisis"],
                                configuracion.leer_secreto, refs, log)
            if nuevo.get("error"):
                log(f"  ✗ {nuevo['error']}")
        if nuevo and not nuevo.get("error"):
            nuevo["fecha"] = datetime.now().isoformat(timespec="minutes")
            _guardar_analisis(nuevo)
            s.analisis = nuevo
            log("  ✓ Análisis listo")
        else:
            # Sin análisis nuevo (no se pidió o falló): se muestra el último que salió bien
            previo = _ultimo_analisis()
            if previo:
                previo["anterior"] = True
                if nuevo and nuevo.get("error"):
                    previo["error_nuevo"] = nuevo["error"]
                s.analisis = previo
                log(f"  Se mantiene el análisis anterior ({previo.get('fecha', 'sin fecha')}).")
            else:
                s.analisis = nuevo

    import fuentes
    datos = {"snapshot": s.to_dict(), "resumen": r, "demo": o.demo, "hoy": date.today().isoformat(),
             "referencias": refs, "historial": historial.por_dia(hist), "entidades": fuentes.nombres()}
    ruta = dashboard.generar(datos, abrir=False)
    log(f"\nDashboard: {Path(ruta).resolve()}")

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
            log(f"  ✗ No pude publicar: {e}")
        finally:
            o.celular_password = None
            o.github_token = None
    return {"dashboard": str(ruta), "datos": datos, "publicado": publicado}
