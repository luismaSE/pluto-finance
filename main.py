#!/usr/bin/env python3
"""Mi cartera desde la terminal. Para la app de escritorio: python app.py

Uso:
  python main.py                          # IOL + PDFs de ./reportes (+ Descargas si está configurado)
  python main.py --reportes ~/resumenes   # otra carpeta o lista de PDFs
  python main.py --sin-iol                # solo PDFs
  python main.py --celular                # además cifra y publica para la app Android
  python main.py --demo                   # datos ficticios
  python main.py --sin-analisis           # sin Claude
"""
import argparse
import webbrowser
from pathlib import Path

import configuracion
from pipeline import Opciones, ejecutar


def main():
    cfg = configuracion.cargar()
    ap = argparse.ArgumentParser()
    ap.add_argument("--reportes", nargs="*", default=[cfg["fuentes"]["reportes"]], help="carpeta(s) o archivos PDF")
    ap.add_argument("--sin-iol", action="store_true")
    ap.add_argument("--sin-descargas", action="store_true", help="no importar desde Descargas")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--sin-analisis", action="store_true")
    ap.add_argument("--modelo", default=cfg["analisis"]["modelo"] or None)
    ap.add_argument("--no-abrir", action="store_true")
    ap.add_argument("--celular", action="store_true", help="cifrar y publicar para la app (ver config.toml)")
    a = ap.parse_args()

    f = cfg["fuentes"]
    o = Opciones(
        reportes=a.reportes,
        descargas=None if (a.sin_descargas or not f["importar_descargas"]) else f["descargas"],
        iol=f["iol"] and not a.sin_iol,
        analisis=cfg["analisis"]["activado"] and not a.sin_analisis,
        modelo=a.modelo,
        celular=a.celular,
        # Si guardaste secretos en el llavero desde la app, la terminal también los usa
        celular_password=configuracion.leer_secreto("celular_password") if a.celular else None,
        github_token=configuracion.leer_secreto("github_token") if a.celular else None,
        referencias=cfg["referencias"],
        publicar=cfg["publicar"],
        demo=a.demo,
    )
    res = ejecutar(o)
    if not a.no_abrir:
        webbrowser.open(Path(res["dashboard"]).resolve().as_uri())
    print("Ojo: el HTML contiene tus datos financieros. Borralo cuando no lo necesites.")


if __name__ == "__main__":
    main()
