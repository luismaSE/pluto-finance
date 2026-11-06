"""API de Anthropic (Claude) con el SDK oficial. Necesita una clave de console.anthropic.com."""
ID = "anthropic"
NOMBRE = "Claude (API de Anthropic)"
DESCRIPCION = "Clave de API de console.anthropic.com. Se cobra por uso."
SECRETO = "ia_anthropic"
ENV = "ANTHROPIC_API_KEY"
MODELO = "claude-opus-5-5"
USA_URL = False
WEB = True           # búsqueda web del lado de Anthropic (herramienta web_search)


def disponible(opciones: dict) -> tuple[bool, str]:
    try:
        import anthropic  # noqa: F401
        return True, "ok"
    except ImportError:
        return False, "Falta la librería: pip install anthropic"


def generar(sistema: str, contenido: str, opciones: dict, clave: str, web: bool = False) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=clave)
    mensajes = [{"role": "user", "content": contenido}]
    extra = {"tools": [{"type": "web_search_20260209", "name": "web_search", "max_uses": 8}]} if web else {}
    try:
        # Streaming para que una respuesta larga no corte por tiempo.
        # fallbacks="default": si el modelo rechaza la consulta, la API la reintenta con otro modelo.
        for _ in range(4):
            with client.beta.messages.stream(
                model=opciones.get("modelo") or MODELO,
                max_tokens=32000,
                system=sistema,
                messages=mensajes,
                output_config={"effort": opciones.get("esfuerzo") or "high"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                **extra,
            ) as stream:
                msg = stream.get_final_message()
            if msg.stop_reason != "pause_turn":
                break
            # la búsqueda web pausó el turno: se reenvía tal cual y el servidor sigue donde quedó
            mensajes = [mensajes[0], {"role": "assistant", "content": msg.content}]
    except anthropic.AuthenticationError:
        raise RuntimeError("Clave de API inválida")
    except anthropic.PermissionDeniedError:
        raise RuntimeError("La clave no tiene permiso para usar ese modelo")
    except anthropic.NotFoundError:
        raise RuntimeError("Modelo inexistente: revisá el nombre del modelo")
    except anthropic.RateLimitError:
        raise RuntimeError("Límite de uso alcanzado: probá de nuevo en un rato")
    except anthropic.APIStatusError as e:
        raise RuntimeError(f"Error de la API ({e.status_code}): {e.message}")
    except anthropic.APIConnectionError:
        raise RuntimeError("No pude conectarme con la API de Anthropic")
    if msg.stop_reason == "refusal":
        raise RuntimeError("El modelo no quiso responder esta consulta")
    return "".join(b.text for b in msg.content if b.type == "text")
