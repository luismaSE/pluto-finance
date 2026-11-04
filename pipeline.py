"""El proceso completo, compartido por la terminal (main.py) y la app de escritorio (escritorio/).

    importar Descargas -> leer PDFs -> IOL -> cotizaciones y tasas -> categorías -> resumen
    -> historial -> análisis de Claude -> dashboard HTML -> (opcional) cifrar y publicar
"""
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import cotizaciones
import dashboard
import historial
import resumen
from categorias import categorizar
from modelo import Snapshot


@dataclass
class Opciones:
    reportes: list = field(default_factory=lambda: ["reportes"])
    descargas: str | None = None          # carpeta de la que se importan resúmenes nuevos
    iol: bool = True
    iol_usuario: str | None = None        # si faltan y iol=True, se piden en la terminal
    iol_clave: str | None = None
    analisis: bool = True
    modelo: str | None = None
    celular: bool = False
    celular_password: str | None = None
    github_token: str | None = None
    referencias: dict = field(default_factory=dict)
    publicar: dict = field(default_factory=dict)
    interactivo: bool = True              # False en la app: nunca usa input()
    demo: bool = False


def _cargar_iol(s: Snapshot, o: Opciones, log):
    log("\n=== IOL ===")
    try:
        from conectores import iol
        c, _, i = iol.obtener(o.iol_usuario, o.iol_clave)
        hoy = date.today().isoformat()
        for x in c + i:
            x.al = x.al or hoy
        s.cuentas += c
        s.inversiones += i
        s.estado_fuentes["IOL"] = {"ok": True, "detalle": f"API en vivo: {len(c)} saldos, {len(i)} posiciones"}
        log(f"  ✓ {len(c)} saldos, {len(i)} posiciones")
    except Exception as e:
        log(f"  ✗ Error en IOL: {e}")
        s.estado_fuentes["IOL"] = {"ok": False, "detalle": str(e)[:200]}
    finally:
        o.iol_clave = None


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
        if o.iol:
            _cargar_iol(s, o, log)

    for m in s.movimientos:
        m.categoria = m.categoria or categorizar(m.descripcion, titulares)
    if not s.cotizaciones.get("mep"):
        s.advertencias.append("Sin cotización MEP: los saldos en USD no se suman al total en pesos.")

    r = resumen.calcular(s)
    hist = historial.cargar() if o.demo else historial.agregar(r, s.estado_fuentes)

    if o.analisis and not o.demo:
        from analisis import analizar
        log("\n=== Análisis de Claude ===")
        s.analisis = analizar(r, s.cotizaciones, o.modelo)
        if s.analisis and not s.analisis.get("error"):
            log("  ✓ Análisis listo")

    datos = {"snapshot": s.to_dict(), "resumen": r, "demo": o.demo, "hoy": date.today().isoformat(),
             "referencias": refs, "historial": historial.por_dia(hist)}
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
