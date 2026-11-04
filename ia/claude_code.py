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


def disponible(opciones: dict) -> tuple[bool, str]:
    if not shutil.which("claude"):
        return False, "No encontré el comando `claude`. Instalá Claude Code y verificá que `claude --version` funcione."
    return True, "ok"


def generar(sistema: str, contenido: str, opciones: dict, clave=None) -> str:
    cmd = [shutil.which("claude"), "-p", sistema, "--output-format", "json"]
    if opciones.get("modelo"):
        cmd += ["--model", opciones["modelo"]]
    p = subprocess.run(cmd, input=contenido, capture_output=True, text=True, timeout=600)
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
