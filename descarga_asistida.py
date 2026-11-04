"""Descarga asistida de resúmenes desde Galicia y Mercado Pago.

Cómo funciona:
1. Se abre un navegador NUEVO y vacío (sin cookies ni sesiones previas) en la web del banco.
2. Vos iniciás sesión: usuario, clave y 2FA los escribís vos; este código no los lee ni los guarda.
3. Descargás (o abrís) los resúmenes en PDF. Cada PDF se captura al vuelo, se identifica por su
   contenido y, si es nuevo, se guarda en reportes/.
4. Al cerrar el navegador se borra la sesión.

Opcional: una "receta" (recetas/<sitio>.json) puede navegar sola hasta los resúmenes después del
login. Se arma una vez para tu cuenta (ver README); si un paso falla, seguís a mano.

Modo "habitual" (el predeterminado para Mercado Pago, que bloquea navegadores automatizados):
se abre la web en TU navegador de siempre, sin ninguna automatización, y la app vigila la
carpeta de Descargas para cargar los resúmenes apenas los bajás.
"""
import hashlib
import json
import re
import shutil
import tempfile
import time
from pathlib import Path

from importar import incorporar

SITIOS = {
    "galicia": {
        "nombre": "Galicia",
        "url": "https://onlinebanking.bancogalicia.com.ar/login",
        "modo": "automatizado",
        "guia_habitual": [
            "Se abrió Galicia en tu navegador de siempre.",
            "Cuentas → Resúmenes e Inversiones → Resúmenes: descargá los PDF.",
            "Apenas lleguen a Descargas los cargo solos. Cuando termines, tocá Listo en la app.",
        ],
        "guia": [
            "Iniciá sesión con tu usuario, clave y token.",
            "Cuentas → Resúmenes: descargá el último de la caja de ahorro en pesos y el de dólares.",
            "Inversiones → Resúmenes / Posición: descargá el PDF de tus fondos.",
            "Cuando termines, cerrá la ventana del navegador.",
        ],
    },
    "mercadopago": {
        "nombre": "Mercado Pago",
        "url": "https://www.mercadopago.com.ar/",
        "modo": "habitual",
        "guia_habitual": [
            "Se abrió Mercado Pago en tu navegador de siempre (si ya tenías sesión, no hace falta loguearte).",
            "Tu dinero → Resúmenes de cuenta (o Actividad → Descargar resumen): elegí el mes y descargá el PDF.",
            "Si dice que el resumen se está generando, esperá a que aparezca y descargalo.",
            "Apenas el PDF llegue a Descargas lo cargo solo. Cuando termines, tocá Listo en la app.",
        ],
        "guia": [
            "Iniciá sesión.",
            "Tu dinero → Resúmenes de cuenta (o Actividad → Descargar resumen): elegí el mes y descargá el PDF.",
            "Si Mercado Pago dice que el resumen se está generando, esperá a que aparezca y descargalo.",
            "Cuando termines, cerrá la ventana del navegador.",
        ],
    },
}


def disponible() -> tuple[bool, str]:
    try:
        import playwright  # noqa: F401
        return True, "ok"
    except ImportError:
        return False, "Falta Playwright: pip install -r requirements-descarga.txt && playwright install chromium"


def _receta(sitio: str) -> list | None:
    p = Path("recetas") / f"{sitio}.json"
    try:
        return json.loads(p.read_text()) if p.exists() else None
    except Exception:
        return None


def _ejecutar_receta(page, pasos: list, log):
    """Pasos: {"esperar_url": regex} | {"ir": url} | {"click": selector} | {"esperar": ms}."""
    log("  Siguiendo la receta guardada (si algo falla, seguí a mano)…")
    for i, paso in enumerate(pasos, 1):
        try:
            if "esperar_url" in paso:
                page.wait_for_url(re.compile(paso["esperar_url"]), timeout=paso.get("timeout", 300_000))
            elif "ir" in paso:
                page.goto(paso["ir"])
            elif "click" in paso:
                page.click(paso["click"], timeout=paso.get("timeout", 20_000))
            elif "esperar" in paso:
                page.wait_for_timeout(paso["esperar"])
        except Exception as e:
            log(f"  · La receta se frenó en el paso {i} ({str(e).splitlines()[0][:80]}). Seguí a mano.")
            return


def sesion(sitio: str, reportes: str, log=print, navegador: str = "chromium",
           url: str | None = None, headless: bool = False, tiempo_max: int = 1200) -> list[str]:
    """Abre el navegador y captura los PDF que descargues o abras. Devuelve los resúmenes nuevos."""
    from playwright.sync_api import sync_playwright

    info = SITIOS[sitio]
    tmp = Path(tempfile.mkdtemp(prefix="cartera-"))
    nuevos, vistos, preparados = [], set(), set()

    def guardar(nombre: str, contenido: bytes):
        if not contenido.startswith(b"%PDF"):
            return
        h = hashlib.sha256(contenido).hexdigest()
        if h in vistos:          # el mismo PDF capturado como descarga y como respuesta
            return
        vistos.add(h)
        archivo = tmp / (re.sub(r"[^\w.-]", "_", nombre or "resumen") or "resumen")
        if archivo.suffix.lower() != ".pdf":
            archivo = archivo.with_suffix(".pdf")
        archivo.write_bytes(contenido)
        n = incorporar(archivo, reportes, log)
        if n:
            nuevos.append(n)
        else:
            log(f"  · {archivo.name}: ya lo tenías o no es un resumen que sepa leer.")

    def on_download(d):
        try:
            destino = tmp / "descarga.tmp"
            d.save_as(destino)
            guardar(d.suggested_filename, destino.read_bytes())
        except Exception as e:
            log(f"  · No pude guardar una descarga: {e}")

    def on_response(r):
        # PDFs que se abren en una pestaña en lugar de descargarse
        try:
            if "application/pdf" in (r.headers.get("content-type") or ""):
                nombre = r.url.split("?")[0].rstrip("/").split("/")[-1] or "resumen.pdf"
                guardar(nombre, r.body())
        except Exception:
            pass

    def preparar(pg):
        if id(pg) not in preparados:
            preparados.add(id(pg))
            pg.on("download", on_download)

    try:
        with sync_playwright() as p:
            opciones = {"headless": headless}
            if navegador in ("chrome", "msedge"):
                opciones["channel"] = navegador
            elif navegador and navegador not in ("chromium", "playwright"):
                opciones["executable_path"] = navegador
            browser = p.chromium.launch(**opciones)
            ctx = browser.new_context(accept_downloads=True, locale="es-AR", no_viewport=True)
            ctx.on("page", preparar)
            ctx.on("response", on_response)
            page = ctx.new_page()
            preparar(page)
            log(f"\n=== Descarga desde {info['nombre']} ===")
            log("  Se abrió un navegador nuevo y vacío. Tu usuario y clave los escribís vos ahí; no se leen ni se guardan.")
            for g in info["guia"]:
                log("  → " + g)
            page.goto(url or info["url"])
            receta = _receta(sitio)
            if receta:
                _ejecutar_receta(page, receta, log)
            inicio = time.time()
            while browser.is_connected() and ctx.pages and time.time() - inicio < tiempo_max:
                try:
                    ctx.pages[0].wait_for_timeout(500)
                except Exception:
                    time.sleep(0.3)
            try:
                ctx.close()
                browser.close()
            except Exception:
                pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    log(f"  Navegador cerrado y sesión descartada. Resúmenes nuevos: {len(nuevos)}")
    return nuevos


def _pdf_completo(p: Path) -> bool:
    """El navegador terminó de escribirlo: empieza con %PDF y tiene el cierre %%EOF."""
    try:
        if p.stat().st_size < 200:
            return False
        with p.open("rb") as f:
            inicio = f.read(5)
            f.seek(-1024, 2)
            fin = f.read()
        return inicio.startswith(b"%PDF") and b"%%EOF" in fin
    except Exception:
        return False


def vigilar(sitio: str, descargas: str, reportes: str, log=print, parar=None,
            tiempo_max: int = 1200, abrir: bool = True) -> list[str]:
    """Abre la web en el navegador habitual (sin automatizar nada) y carga los PDF
    que aparezcan en Descargas mientras tanto. Termina con `parar.set()` o por tiempo."""
    import threading
    import webbrowser
    info = SITIOS[sitio]
    carpeta = Path(descargas).expanduser()
    if not carpeta.is_dir():
        raise RuntimeError(f"La carpeta de descargas {carpeta} no existe: revisala en Configuración")
    parar = parar or threading.Event()
    log(f"\n=== {info['nombre']} en tu navegador ===")
    for g in info.get("guia_habitual", []):
        log("  → " + g)
    log(f"  Vigilando {carpeta}…")
    inicio = time.time() - 5
    if abrir:
        webbrowser.open(info["url"])
    procesados, nuevos = set(), []
    while not parar.is_set() and time.time() - inicio < tiempo_max:
        for p in carpeta.glob("*.pdf"):
            try:
                if p in procesados or p.stat().st_mtime < inicio or not _pdf_completo(p):
                    continue
            except OSError:
                continue
            procesados.add(p)
            n = incorporar(p, reportes, log)
            if n:
                nuevos.append(n)
            else:
                log(f"  · {p.name}: ya lo tenías o no es un resumen que sepa leer.")
        parar.wait(1.5)
    log(f"  Listo. Resúmenes nuevos: {len(nuevos)}")
    return nuevos


if __name__ == "__main__":
    import sys
    import configuracion
    if len(sys.argv) < 2 or sys.argv[1] not in SITIOS:
        sys.exit(f"Uso: python descarga_asistida.py {'|'.join(SITIOS)}")
    cfg = configuracion.cargar()
    modo = cfg["descarga"].get(f"modo_{sys.argv[1]}") or SITIOS[sys.argv[1]]["modo"]
    if modo == "habitual":
        import threading
        parar = threading.Event()
        threading.Thread(target=lambda: (input("Presioná Enter cuando termines de descargar…\n"), parar.set()), daemon=True).start()
        vigilar(sys.argv[1], cfg["fuentes"]["descargas"], cfg["fuentes"]["reportes"], parar=parar)
    else:
        sesion(sys.argv[1], cfg["fuentes"]["reportes"], navegador=cfg["descarga"].get("navegador", "chromium"))
