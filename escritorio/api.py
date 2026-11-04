"""Funciones que la interfaz (ui.html) puede llamar desde JavaScript.

Reglas de seguridad:
- Ningún método devuelve secretos: solo si están guardados o no.
- La clave de IOL llega para una corrida, se usa y se descarta (nunca se guarda).
- El dashboard se abre en una ventana aparte que NO tiene acceso a esta API.
"""
import glob
import os
import threading
import traceback
import webbrowser
from pathlib import Path

import configuracion
import historial

VERSION = "1.1.0"


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
        return {
            "version": VERSION,
            "config": cfg,
            "secretos": {k: {"descripcion": d, "guardado": bool(configuracion.leer_secreto(k)) if ok else False}
                         for k, d in configuracion.SECRETOS.items()},
            "llavero": {"ok": ok, "detalle": detalle},
            "historial": h[-30:][::-1],
            "dashboard": bool(self._ultimo_dashboard()),
            "corriendo": self._corriendo.locked(),
            "carpeta": str(Path.cwd()),
        }

    # ---------- configuración ----------
    def guardar_config(self, cfg: dict) -> dict:
        base = configuracion.cargar()
        configuracion._mezclar(base, cfg)
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
            return {"ok": False, "mensaje": str(e)}

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
                iol=bool(op.get("iol")) and bool(op.get("iol_usuario")) and bool(op.get("iol_clave")),
                iol_usuario=op.get("iol_usuario"),
                iol_clave=op.get("iol_clave"),
                analisis=bool(op.get("analisis")),
                modelo=cfg["analisis"].get("modelo") or None,
                celular=celular,
                celular_password=configuracion.leer_secreto("celular_password") if celular else None,
                github_token=configuracion.leer_secreto("github_token") if celular else None,
                referencias=cfg["referencias"],
                publicar=cfg["publicar"],
                interactivo=False,
            )
            op.clear()   # descarta la clave de IOL de este diccionario
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

    # ---------- dashboard ----------
    def _ultimo_dashboard(self) -> Path | None:
        archivos = sorted(glob.glob("salida/dashboard_*.html"), key=os.path.getmtime)
        return Path(archivos[-1]) if archivos else None

    def dashboard_html(self) -> str | None:
        p = self._ultimo_dashboard()
        return p.read_text(encoding="utf-8") if p else None

    def abrir_dashboard_ventana(self) -> dict:
        """Ventana nueva sin js_api: el dashboard no puede llamar a nada de Python."""
        import webview
        html = self.dashboard_html()
        if not html:
            return {"ok": False}
        webview.create_window("Mi cartera · Dashboard", html=html, width=1280, height=900, min_size=(380, 600))
        return {"ok": True}

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
