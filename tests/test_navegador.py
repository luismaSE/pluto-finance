"""El dashboard abierto en un navegador de verdad: ninguna pestaña puede tirar errores de JavaScript.

Necesita Playwright (pip install playwright && python -m playwright install chromium).
Si no está, estas pruebas se saltean; en GitHub son obligatorias (PLUTO_NAVEGADOR=1).
Para usar otro Chromium: PLUTO_CHROMIUM=/ruta/al/ejecutable.
"""
import copy
import os
from pathlib import Path

import pytest

PESTANAS = ["resumen", "gastos", "inversiones", "analisis", "mercado"]


@pytest.fixture(scope="module")
def navegador():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if os.environ.get("PLUTO_NAVEGADOR"):
            raise
        pytest.skip("Playwright no está instalado")
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=os.environ.get("PLUTO_CHROMIUM") or None)
        except Exception as e:
            if os.environ.get("PLUTO_NAVEGADOR"):
                raise
            pytest.skip(f"No pude abrir Chromium: {str(e).splitlines()[0]}")
        yield b
        b.close()


@pytest.fixture(scope="module")
def datos_demo(tmp_path_factory):
    import pipeline
    anterior = os.getcwd()
    os.chdir(tmp_path_factory.mktemp("demo"))
    try:
        return pipeline.ejecutar(pipeline.Opciones(demo=True, analisis=False), log=lambda *_: None)["datos"]
    finally:
        os.chdir(anterior)


def abrir(navegador, datos, carpeta: Path, ancho=1200, alto=900, tema=None):
    import dashboard
    ruta = dashboard.generar(datos, carpeta / "d.html", abrir=False)
    pagina = navegador.new_page(viewport={"width": ancho, "height": alto})
    errores = []
    pagina.on("pageerror", lambda e: errores.append(str(e)))
    pagina.on("console", lambda m: m.type == "error" and errores.append(m.text))
    if tema:
        pagina.add_init_script(f"localStorage.setItem('tema', '{tema}')")
    pagina.goto(Path(ruta).resolve().as_uri())
    return pagina, errores


def recorrer(pagina, pestanas=PESTANAS):
    for t in pestanas:
        pagina.click(f'[data-tab="{t}"]')
        assert pagina.locator(f"#p-{t}").is_visible()
        assert pagina.locator(f"#p-{t}").inner_text().strip(), f"la pestaña {t} quedó vacía"


def test_todas_las_pestanas_sin_errores(navegador, datos_demo, tmp_path):
    pagina, errores = abrir(navegador, datos_demo, tmp_path)
    recorrer(pagina)
    pagina.click('[data-tab="analisis"]')
    assert pagina.locator("#p-analisis .anillo").count() == 1 and pagina.locator("#p-analisis .tile").count() == 4
    pagina.click('[data-tab="mercado"]')
    m = pagina.locator("#p-mercado")
    assert m.locator(".reco-t").count() == 3 and m.locator(".stack100").count() == 2
    assert m.locator(".spark").count() == len(datos_demo["mercado"]["precios"])
    assert "no opera" in m.locator(".solo-lectura").inner_text()
    # los detalles plegados se abren al tocar
    d = m.locator(".reco-t details").first
    d.locator("summary").click()
    assert d.get_attribute("open") is not None
    assert errores == []
    pagina.close()


def test_celular_sin_scroll_horizontal(navegador, datos_demo, tmp_path):
    pagina, errores = abrir(navegador, datos_demo, tmp_path, ancho=360, alto=740)
    for t in PESTANAS:
        pagina.click(f'[data-tab="{t}"]')
        ancho = pagina.evaluate("document.documentElement.scrollWidth")
        assert ancho <= 360, f"la pestaña {t} se sale del ancho del celular ({ancho}px)"
    assert errores == []
    pagina.close()


def test_modo_claro(navegador, datos_demo, tmp_path):
    pagina, errores = abrir(navegador, datos_demo, tmp_path, tema="light")
    assert pagina.evaluate("document.documentElement.dataset.theme") == "light"
    recorrer(pagina)
    assert errores == []
    pagina.close()


def test_analisis_en_formato_anterior(navegador, datos_demo, tmp_path):
    """Un análisis guardado antes del rediseño (sin titular, puntaje ni termómetro) se sigue viendo."""
    d = copy.deepcopy(datos_demo)
    for k in ("titular", "salud", "indicadores"):
        d["snapshot"]["analisis"].pop(k, None)
    a = d["mercado"]["analisis"]
    for k in ("titular", "puntos_clave", "termometro"):
        a.pop(k, None)
    for e in a["escenarios"]:
        e["efecto"] = e.pop("detalle")
    for r in a["recomendaciones"]:
        r.pop("titulo")
    pagina, errores = abrir(navegador, d, tmp_path)
    recorrer(pagina)
    assert pagina.locator("#p-mercado .titular").first.inner_text().startswith("Datos ficticios")
    assert errores == []
    pagina.close()


def test_sin_analisis_ni_mercado(navegador, datos_demo, tmp_path):
    d = copy.deepcopy(datos_demo)
    d["snapshot"]["analisis"] = None
    d["mercado"] = None
    pagina, errores = abrir(navegador, d, tmp_path)
    assert not pagina.locator('[data-tab="mercado"]').is_visible()
    recorrer(pagina, PESTANAS[:-1])
    assert errores == []
    pagina.close()


def test_analisis_con_error(navegador, datos_demo, tmp_path):
    d = copy.deepcopy(datos_demo)
    d["snapshot"]["analisis"] = {"error": "Clave inválida"}
    d["mercado"]["analisis"] = {"error": "Sin conexión"}
    pagina, errores = abrir(navegador, d, tmp_path)
    recorrer(pagina)
    assert "Clave inválida" in pagina.locator("#p-analisis").inner_text()
    assert "Sin conexión" in pagina.locator("#p-mercado").inner_text()
    assert errores == []
    pagina.close()


def test_la_app_abre_una_pestana(navegador, datos_demo, tmp_path):
    """La app de escritorio pide abrir Mercado con postMessage; un nombre inválido no hace nada."""
    pagina, errores = abrir(navegador, datos_demo, tmp_path)
    pagina.evaluate("window.postMessage({ir: 'mercado'}, '*')")
    pagina.wait_for_function("!document.getElementById('p-mercado').hidden")
    pagina.evaluate("window.postMessage({ir: '\"]x'}, '*'); window.postMessage('basura', '*')")
    pagina.wait_for_timeout(100)
    assert pagina.locator("#p-mercado").is_visible() and errores == []
    pagina.close()


def test_le_ganas_a_la_inflacion(navegador, datos_demo, tmp_path):
    pagina, errores = abrir(navegador, datos_demo, tmp_path)
    t = pagina.locator("#p-resumen").inner_text()
    assert "inflación" in t and pagina.locator("#p-resumen .infla-ver").count() == 1
    assert pagina.locator("#p-resumen .linea-punt").count() == 1       # línea "para empatar"
    d = copy.deepcopy(datos_demo)
    d["resumen"]["contra_inflacion"] = {"faltan_dias": 3, "desde": "2026-01-01"}
    pagina2, errores2 = abrir(navegador, d, tmp_path)
    assert "En 3 días" in pagina2.locator("#p-resumen").inner_text()
    assert errores == [] and errores2 == []
    pagina.close(); pagina2.close()


def test_metas_de_ahorro(navegador, datos_demo, tmp_path):
    pagina, errores = abrir(navegador, datos_demo, tmp_path)
    t = pagina.locator("#p-resumen").inner_text()
    assert "metas de ahorro" in t.lower() and "Atrasada" in t and "En camino" in t
    assert pagina.locator("#p-resumen .meta-f").count() == 3 and errores == []
    pagina.close()
