"""Ollama: modelos que corren en tu propia computadora. Los datos no salen de tu equipo."""
import requests

ID = "ollama"
NOMBRE = "Ollama (local)"
DESCRIPCION = "Modelos que corren en tu computadora (ollama.com). Los datos no salen de tu equipo."
SECRETO = None
MODELO = "llama3.1"
USA_URL = True
URL = "http://localhost:11434"


def disponible(opciones: dict) -> tuple[bool, str]:
    url = (opciones.get("url") or URL).rstrip("/")
    try:
        r = requests.get(url + "/api/tags", timeout=5)
        r.raise_for_status()
    except Exception:
        return False, f"No encuentro Ollama en {url}. ¿Está instalado y corriendo (`ollama serve`)?"
    modelos = [m.get("name", "") for m in r.json().get("models", [])]
    m = opciones.get("modelo") or MODELO
    if modelos and not any(x == m or x.startswith(m + ":") for x in modelos):
        return False, f"El modelo {m} no está descargado. Corré `ollama pull {m}` (tenés: {', '.join(modelos[:5])})"
    return True, "ok"


def generar(sistema: str, contenido: str, opciones: dict, clave=None) -> str:
    url = (opciones.get("url") or URL).rstrip("/") + "/api/chat"
    r = requests.post(url, timeout=900, json={
        "model": opciones.get("modelo") or MODELO,
        "stream": False,
        "format": "json",
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": contenido}],
    })
    if r.status_code >= 400:
        raise RuntimeError(f"Ollama respondió {r.status_code}: {r.text[:200]}")
    return r.json().get("message", {}).get("content", "")
