"""Funciones que la interfaz (escritorio/ui/) puede llamar desde JavaScript.

Reglas de seguridad:
- Ningún método devuelve secretos: solo si están guardados o no.
- La clave de IOL llega para una corrida, se usa y se descarta (nunca se guarda).
- El dashboard se muestra en un iframe con sandbox (origen opaco): no puede leer la app
  ni llamar a esta API, y su política de contenido le impide conectarse a internet.
"""
import glob
import os
import threading
import traceback
import webbrowser
from pathlib import Path

import configuracion
import historial

VERSION = (Path(__file__).resolve().parent.parent / "VERSION").read_text().strip() if (Path(__file__).resolve().parent.parent / "VERSION").exists() else "dev"


class Api:
    def __init__(self):
        self._ventana = None
        self._corriendo = threading.Lock()

    # pywebview expone todos los métodos públicos; los internos empiezan con "_"
    def _set_ventana(self, v):
        self._ventana = v

    def _js(self, codigo: str):
        if self._ventana:
            try:
                self._ventana.evaluate_js(codigo)
            except Exception:
                pass

    def _log(self, texto: str):
        import json
        self._js(f"ui.log({json.dumps(str(texto))})")

    # ---------- estado ----------
    def estado(self) -> dict:
        cfg = configuracion.cargar()
        ok, detalle = configuracion.llavero_disponible()
        h = historial.cargar()
        import fuentes
        import ia
        return {
            "version": VERSION,
            "primer_uso": configuracion.primer_uso(),
            "config": cfg,
            "fuentes": fuentes.catalogo(cfg),
            "descarga_sitios": [{"id": k, "nombre": v["nombre"]} for k, v in __import__("descarga_asistida").SITIOS.items()],
            "proveedores_ia": [{"id": m.ID, "nombre": m.NOMBRE, "descripcion": m.DESCRIPCION, "secreto": m.SECRETO,
                                "modelo": m.MODELO, "usa_url": m.USA_URL} for m in ia.PROVEEDORES.values()],
            "secretos": {k: {"descripcion": d, "guardado": bool(configuracion.leer_secreto(k)) if ok else False}
                         for k, d in configuracion.SECRETOS.items()},
            "llavero": {"ok": ok, "detalle": detalle},
            "historial": h[-30:][::-1],
            "dashboard": bool(self._ultimo_dashboard()),
            "corriendo": self._corriendo.locked(),
            "categorias": __import__("categorias").CATEGORIAS,
            "carpeta": str(Path.cwd()),
        }

    # ---------- configuración ----------
    def guardar_config(self, cfg: dict) -> dict:
        base = configuracion.cargar()
        configuracion._mezclar(base, cfg)
        configuracion.guardar(base)
        return {"ok": True}

    # Secciones que se guardan completas (no se mezclan): así se pueden borrar límites y tarjetas
    _REEMPLAZABLES = {"presupuestos", "tarjetas"}

    def reemplazar_config(self, seccion: str, valor: dict) -> dict:
        if seccion not in self._REEMPLAZABLES:
            return {"ok": False, "error": "Sección no permitida"}
        base = configuracion.cargar()
        base[seccion] = valor or {}
        configuracion.guardar(base)
        return {"ok": True}

    # ---------- categorías ----------
    def _ultimos_datos(self) -> dict | None:
        """Datos del último dashboard generado (para listar movimientos a corregir)."""
        import json
        import re
        p = self._ultimo_dashboard()
        if not p:
            return None
        m = re.search(r"const DATA = (.*?);\n", p.read_text(encoding="utf-8"))
        try:
            return json.loads(m.group(1)) if m else None
        except ValueError:
            return None

    def categorias(self) -> dict:
        import categorias as cat
        datos = self._ultimos_datos() or {}
        reglas = configuracion.cargar()["categorias"].get("reglas", {})
        movs = [m for m in (datos.get("snapshot") or {}).get("movimientos", []) if m.get("categoria") != "Rendimientos"]
        vistos, lista = set(), []
        for m in sorted(movs, key=lambda m: m["fecha"], reverse=True):
            clave = cat.clave_regla(m["descripcion"])
            if clave in vistos:
                continue
            vistos.add(clave)
            lista.append({"clave": clave, "descripcion": m["descripcion"], "fecha": m["fecha"], "monto": m["monto"],
                          "moneda": m["moneda"], "entidad": m["entidad"], "categoria": reglas.get(clave, m.get("categoria") or "Otros"),
                          "propia": clave in reglas})
        return {"categorias": cat.CATEGORIAS, "movimientos": lista[:300], "reglas": reglas,
                "excluidas": sorted(cat.EXCLUIDAS), "hay_datos": bool(datos)}

    def guardar_regla(self, descripcion: str, categoria: str) -> dict:
        import categorias as cat
        if categoria not in cat.CATEGORIAS:
            return {"ok": False, "error": "Categoría desconocida"}
        base = configuracion.cargar()
        base["categorias"].setdefault("reglas", {})[cat.clave_regla(descripcion)] = categoria
        configuracion.guardar(base)
        return {"ok": True}

    def borrar_regla(self, clave: str) -> dict:
        base = configuracion.cargar()
        base["categorias"].get("reglas", {}).pop(clave, None)
        configuracion.guardar(base)
        return {"ok": True}

    def guardar_secreto(self, nombre: str, valor: str) -> dict:
        if nombre not in configuracion.SECRETOS:
            return {"ok": False, "error": "Secreto desconocido"}
        if nombre == "celular_password" and len(valor or "") < 12:
            return {"ok": False, "error": "La contraseña tiene que tener al menos 12 caracteres"}
        if not valor:
            return {"ok": False, "error": "Vacío"}
        try:
            configuracion.guardar_secreto(nombre, valor)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def borrar_secreto(self, nombre: str) -> dict:
        configuracion.borrar_secreto(nombre)
        return {"ok": True}

    def probar_ia(self) -> dict:
        """Prueba corta del proveedor de IA configurado (no manda datos personales)."""
        import ia
        return ia.probar(configuracion.cargar()["analisis"], configuracion.leer_secreto)

    def probar_github(self) -> dict:
        import publicar
        cfg = configuracion.cargar()["publicar"]["github"]
        if not cfg.get("repo"):
            return {"ok": False, "mensaje": "Completá el repositorio"}
        token = configuracion.leer_secreto("github_token") or os.environ.get(cfg.get("token_env", ""))
        if not token:
            return {"ok": False, "mensaje": "Guardá primero el token de GitHub"}
        try:
            return {"ok": True, "mensaje": publicar.probar_github(cfg, token)}
        except Exception as e:
            from utils import mensaje_error
            return {"ok": False, "mensaje": mensaje_error(e, "GitHub")}

    def elegir_carpeta(self) -> str | None:
        import webview
        r = self._ventana.create_file_dialog(webview.FOLDER_DIALOG)
        return r[0] if r else None

    def elegir_archivo(self) -> str | None:
        import webview
        r = self._ventana.create_file_dialog(webview.OPEN_DIALOG, file_types=("JSON (*.json)",))
        return r[0] if r else None

    # ---------- actualizar ----------
    def actualizar(self, opciones: dict) -> dict:
        """Lanza el proceso completo en segundo plano. El progreso llega a ui.log()."""
        if not self._corriendo.acquire(blocking=False):
            return {"ok": False, "error": "Ya hay una actualización en curso"}
        threading.Thread(target=self._correr, args=(dict(opciones or {}),), daemon=True).start()
        return {"ok": True}

    def _correr(self, op: dict):
        from pipeline import Opciones, ejecutar
        resultado = {"ok": False}
        try:
            cfg = configuracion.cargar()
            f = cfg["fuentes"]
            celular = bool(op.get("celular"))
            o = Opciones(
                reportes=[f["reportes"]],
                descargas=f["descargas"] if f.get("importar_descargas") else None,
                # {"iol": {"usuario": ..., "clave": ...}} solo de los brokers que el usuario completó
                brokers={k: v for k, v in (op.get("brokers") or {}).items() if v} if op.get("consultar_brokers") else {},
                analisis=bool(op.get("analisis")),
                ia=cfg["analisis"],
                celular=celular,
                celular_password=configuracion.leer_secreto("celular_password") if celular else None,
                github_token=configuracion.leer_secreto("github_token") if celular else None,
                referencias=cfg["referencias"],
                publicar=cfg["publicar"],
                interactivo=False,
            )
            op.clear()   # descarta las credenciales de los brokers de este diccionario
            r = ejecutar(o, log=self._log)
            resultado = {"ok": True, "publicado": r["publicado"], "celular": celular}
        except Exception as e:
            self._log(f"✗ Error inesperado: {e}")
            self._log(traceback.format_exc(limit=3))
            resultado = {"ok": False, "error": str(e)}
        finally:
            self._corriendo.release()
            import json
            self._js(f"ui.fin({json.dumps(resultado)})")

    # ---------- descarga asistida ----------
    def descarga_disponible(self) -> dict:
        import descarga_asistida
        ok, detalle = descarga_asistida.disponible()
        return {"ok": ok, "detalle": detalle}

    def descargar(self, sitio: str) -> dict:
        """Abre el navegador en Galicia para bajar resúmenes. Progreso en ui.log()."""
        import descarga_asistida
        if sitio not in descarga_asistida.SITIOS:
            return {"ok": False, "error": "Sitio desconocido"}
        ok, detalle = descarga_asistida.disponible()
        if not ok:
            return {"ok": False, "error": detalle}
        if not self._corriendo.acquire(blocking=False):
            return {"ok": False, "error": "Hay otra tarea en curso"}
        threading.Thread(target=self._descargar, args=(sitio,), daemon=True).start()
        return {"ok": True}

    def _descargar(self, sitio: str):
        import json
        import descarga_asistida
        res = {"ok": False, "nuevos": []}
        try:
            cfg = configuracion.cargar()
            nuevos = descarga_asistida.sesion(sitio, cfg["fuentes"]["reportes"], log=self._log,
                                              navegador=cfg["descarga"].get("navegador") or "chromium")
            res = {"ok": True, "nuevos": nuevos}
        except Exception as e:
            msg = str(e).splitlines()[0]
            if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
                msg = "Falta el navegador de Playwright: corré `playwright install chromium`"
            self._log(f"✗ {msg}")
            res = {"ok": False, "error": msg, "nuevos": []}
        finally:
            self._corriendo.release()
            self._js(f"ui.finDescarga({json.dumps(res)})")

    # ---------- dashboard ----------
    def _ultimo_dashboard(self) -> Path | None:
        archivos = sorted(glob.glob("salida/dashboard_*.html"), key=os.path.getmtime)
        return Path(archivos[-1]) if archivos else None

    def dashboard_html(self) -> str | None:
        p = self._ultimo_dashboard()
        return p.read_text(encoding="utf-8") if p else None

    def abrir_dashboard_navegador(self) -> dict:
        p = self._ultimo_dashboard()
        if p:
            webbrowser.open(p.resolve().as_uri())
        return {"ok": bool(p)}

    def abrir_carpeta(self, cual: str) -> dict:
        import subprocess
        import sys
        cfg = configuracion.cargar()["fuentes"]
        ruta = {"salida": "salida", "reportes": cfg["reportes"], "descargas": cfg["descargas"]}.get(cual, "salida")
        ruta = Path(ruta).expanduser()
        ruta.mkdir(exist_ok=True, parents=True)
        cmd = {"win32": ["explorer"], "darwin": ["open"]}.get(sys.platform, ["xdg-open"])
        subprocess.Popen(cmd + [str(ruta)])
        return {"ok": True}
