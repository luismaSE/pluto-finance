from pathlib import Path

from plantillas.ensamblar import RAIZ, dashboard


def test_dashboard_armado_al_dia():
    """plantillas/dashboard.html (lo usa la app Android) tiene que coincidir con plantillas/dashboard/.
    Si falla: python plantillas/ensamblar.py"""
    assert (RAIZ / "plantillas" / "dashboard.html").read_text(encoding="utf-8") == dashboard()


def test_marcadores_presentes():
    html = dashboard()
    assert "/*__DATOS__*/null" in html and "/*__FUENTES__*/" in html and "font-src data:" in html


def test_genera_dashboard_demo(carpeta):
    import dashboard as d
    ruta = d.generar({"snapshot": {}, "resumen": {}, "demo": True}, Path("salida/x.html"), abrir=False)
    html = Path(ruta).read_text(encoding="utf-8")
    assert "/*__FUENTES__*/" not in html and "Bricolage Grotesque" in html
