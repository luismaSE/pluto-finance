"""Claude Code (comando `claude`): usa tu sesión de Claude Code, sin clave aparte."""
import json
import shutil
import subprocess

ID = "claude_code"
NOMBRE = "Claude Code"
DESCRIPCION = "Usa el comando `claude` con tu sesión iniciada. No necesita clave."
SECRETO = None
MODELO = ""          # vacío = el modelo por defecto de Claude Code; también acepta "opus", "sonnet", "haiku"
USA_URL = False
WEB = True           # puede buscar noticias en la web (herramienta WebSearch de Claude Code)


def disponible(opciones: dict) -> tuple[bool, str]:
    if not shutil.which("claude"):
        return False, "No encontré el comando `claude`. Instalá Claude Code y verificá que `claude --version` funcione."
    return True, "ok"


def generar(sistema: str, contenido: str, opciones: dict, clave=None, web: bool = False) -> str:
    cmd = [shutil.which("claude"), "-p", sistema, "--output-format", "json"]
    if web:
        # Solo búsqueda web (lectura). No se habilita ninguna herramienta que modifique nada.
        cmd += ["--allowedTools", "WebSearch"]
    if opciones.get("modelo"):
        cmd += ["--model", opciones["modelo"]]
    # Nunca puede modificar nada, y corre en una carpeta vacía: no ve tus archivos ni tus resúmenes
    cmd += ["--disallowedTools", "Bash", "Edit", "Write", "NotebookEdit", "Read", "Glob", "Grep"]
    import tempfile
    with tempfile.TemporaryDirectory(prefix="pluto-ia-") as vacia:
        p = subprocess.run(cmd, input=contenido, capture_output=True, text=True,
                           timeout=900 if web else 600, cwd=vacia)
    try:
        salida = json.loads(p.stdout)
    except ValueError:
        raise RuntimeError(f"respuesta inesperada: {(p.stderr or p.stdout).strip()[:300] or p.returncode}")
    texto = salida.get("result") or ""
    if p.returncode != 0 or salida.get("is_error"):
        msg = texto or (p.stderr or "").strip()[:300] or f"código {p.returncode}"
        if any(k in msg.lower() for k in ("login", "auth", "api key", "oauth")):
            msg += " → corré `claude` en una terminal e iniciá sesión (/login)."
        raise RuntimeError(msg)
    return texto
