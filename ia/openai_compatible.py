"""Cualquier servicio con API compatible con OpenAI (Chat Completions).

Sirve para OpenAI, OpenRouter, Groq, Google Gemini (endpoint compatible), LM Studio, etc.
Se configura la dirección del servidor, el modelo y la clave.
"""
import requests

ID = "openai_compatible"
NOMBRE = "API compatible con OpenAI"
DESCRIPCION = "OpenAI, OpenRouter, Gemini, LM Studio u otro servicio compatible. Configurás dirección, modelo y clave."
SECRETO = "ia_openai"
ENV = "OPENAI_API_KEY"
MODELO = ""
USA_URL = True
URL = "https://api.openai.com/v1"


def disponible(opciones: dict) -> tuple[bool, str]:
    if not opciones.get("modelo"):
        return False, "Indicá el modelo a usar (Configuración → Análisis)"
    return True, "ok"


def generar(sistema: str, contenido: str, opciones: dict, clave: str) -> str:
    url = (opciones.get("url") or URL).rstrip("/") + "/chat/completions"
    r = requests.post(url, timeout=600, headers={"Authorization": f"Bearer {clave}"}, json={
        "model": opciones["modelo"],
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": contenido}],
    })
    if r.status_code == 401:
        raise RuntimeError("Clave inválida")
    if r.status_code >= 400:
        raise RuntimeError(f"El servicio respondió {r.status_code}: {r.text[:200]}")
    return r.json()["choices"][0]["message"]["content"] or ""
