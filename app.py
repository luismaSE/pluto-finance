#!/usr/bin/env python3
"""Mi cartera - app de escritorio.

    python app.py

Ventana propia (pywebview): no abre puertos ni levanta servidores.
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
os.chdir(RAIZ)
sys.path.insert(0, str(RAIZ))


def main():
    try:
        import webview
    except ImportError:
        sys.exit("Falta pywebview. Instalá las dependencias: pip install -r requirements-escritorio.txt")
    from escritorio.api import Api

    api = Api()
    html = (RAIZ / "escritorio" / "ui.html").read_text(encoding="utf-8")
    ventana = webview.create_window("Mi cartera", html=html, js_api=api, width=1240, height=860, min_size=(900, 640))
    api._set_ventana(ventana)
    webview.start(private_mode=True, debug="--debug" in sys.argv)


if __name__ == "__main__":
    main()
