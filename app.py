#!/usr/bin/env python3
"""Pluto - app de escritorio.

    python app.py

Ventana propia (pywebview): no abre puertos ni levanta servidores.
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
os.chdir(RAIZ)
sys.path.insert(0, str(RAIZ))


def interfaz() -> str:
    """Interfaz armada desde escritorio/ui/, con las tipografías incrustadas (funciona sin internet)."""
    from plantillas.ensamblar import ensamblar
    html = ensamblar(RAIZ / "escritorio" / "ui")
    fuentes = RAIZ / "plantillas" / "fuentes.css"
    if fuentes.exists():
        html = html.replace("/*__FUENTES__*/", fuentes.read_text(encoding="utf-8"), 1)
    return html


def main():
    try:
        import webview
    except ImportError:
        sys.exit("Falta pywebview. Instalá las dependencias: pip install -r requirements-escritorio.txt")
    from escritorio.api import Api

    api = Api()
    ventana = webview.create_window("Pluto", html=interfaz(), js_api=api, width=1240, height=860,
                                    min_size=(900, 640), background_color="#1b2227")
    api._set_ventana(ventana)
    icono = RAIZ / "marca" / "icono-256.png"
    try:   # `icon` existe desde pywebview 5 (Linux); en versiones viejas se arranca sin ícono
        webview.start(private_mode=True, debug="--debug" in sys.argv, icon=str(icono) if icono.exists() else None)
    except TypeError:
        webview.start(private_mode=True, debug="--debug" in sys.argv)


if __name__ == "__main__":
    main()
