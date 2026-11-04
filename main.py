#!/usr/bin/env python3
"""Estado de cartera consolidado: IOL (API) + resúmenes PDF de Galicia y Mercado Pago
-> análisis de Claude -> dashboard HTML.

Uso:
  python main.py                          # IOL + todos los PDF de ./reportes
  python main.py --reportes ~/Descargas/resumenes   # otra carpeta o lista de PDFs
  python main.py --sin-iol                # solo PDFs
  python main.py --demo                   # datos ficticios
  python main.py --sin-analisis           # sin Claude
  python main.py --celular                # además cifra y publica para la app Android

No se guardan credenciales: la clave de IOL se pide en la terminal y se descarta.
"""
import argparse
from datetime import date

import cotizaciones
import dashboard
import resumen
from analisis import analizar
from categorias import categorizar
from modelo import Snapshot


def cargar_iol(s: Snapshot):
    print("\n=== IOL ===")
    try:
        from conectores import iol
        c, m, i = iol.obtener()
        hoy = date.today().isoformat()
        for x in c + i:
            x.al = x.al or hoy
        s.cuentas += c
        s.inversiones += i
        s.estado_fuentes["IOL"] = {"ok": True, "detalle": f"API en vivo: {len(c)} saldos, {len(i)} posiciones"}
    except KeyboardInterrupt:
        s.estado_fuentes["IOL"] = {"ok": False, "detalle": "Omitido por el usuario"}
    except Exception as e:
        print(f"  Error en IOL: {e}")
        s.estado_fuentes["IOL"] = {"ok": False, "detalle": str(e)[:200]}


def cargar_pdfs(s: Snapshot, rutas) -> set:
    from conectores import pdf
    titulares, detalle = set(), {}
    archivos = pdf.archivos(rutas)
    print(f"\n=== Reportes PDF ({len(archivos)}) ===")
    if not archivos:
        print("  No encontré PDFs. Descargá los resúmenes y ponelos en ./reportes")
    for f in archivos:
        try:
            r = pdf.leer(f)
        except Exception as e:
            print(f"  ✗ {f.name}: {e}")
            s.advertencias.append(f"No pude leer {f.name}: {e}")
            continue
        print(f"  ✓ {f.name}: {r.entidad} · {r.descripcion} · {len(r.movimientos)} movimientos")
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reportes", nargs="*", default=["reportes"], help="carpeta(s) o archivos PDF")
    ap.add_argument("--sin-iol", action="store_true")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--sin-analisis", action="store_true")
    ap.add_argument("--modelo", help="modelo para Claude Code, ej. opus o sonnet")
    ap.add_argument("--no-abrir", action="store_true")
    ap.add_argument("--celular", action="store_true", help="cifrar y publicar para la app (ver config.toml)")
    a = ap.parse_args()

    titulares = set()
    if a.demo:
        from demo import snapshot_demo
        s = snapshot_demo()
    else:
        s = Snapshot()
        s.cotizaciones = cotizaciones.obtener()
        titulares = cargar_pdfs(s, a.reportes)
        if not a.sin_iol:
            cargar_iol(s)

    for m in s.movimientos:
        m.categoria = m.categoria or categorizar(m.descripcion, titulares)
    if not s.cotizaciones.get("mep"):
        s.advertencias.append("Sin cotización MEP: los saldos en USD no se suman al total en pesos.")

    r = resumen.calcular(s)
    if not a.demo and not a.sin_analisis:
        s.analisis = analizar(r, s.cotizaciones, a.modelo)

    datos = {"snapshot": s.to_dict(), "resumen": r, "demo": a.demo, "hoy": date.today().isoformat()}
    if a.celular:
        import cifrado
        import publicar
        print("\n=== Celular ===")
        try:
            publicar.publicar(cifrado.cifrar(datos, cifrado.pedir_password()))
        except Exception as e:
            print(f"  ✗ No pude publicar: {e}")
    p = dashboard.generar(datos, abrir=not a.no_abrir)
    print(f"\nDashboard: {p.resolve()}")
    print("Ojo: el HTML contiene tus datos financieros. Borralo cuando no lo necesites.")


if __name__ == "__main__":
    main()
