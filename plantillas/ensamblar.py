"""Arma una página HTML a partir de su carpeta: index.html + estilos.css + app.js.

- El dashboard (plantillas/dashboard/) se arma en plantillas/dashboard.html, que es el archivo
  que usan la PC y la app Android. Después de cambiar algo en la carpeta, corré:
      python plantillas/ensamblar.py
  (una prueba automática verifica que dashboard.html esté al día).
- La interfaz de escritorio (escritorio/ui/) se arma al abrir la app.
Las tipografías (/*__FUENTES__*/) y los datos (/*__DATOS__*/) se insertan después, al usarla.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def ensamblar(carpeta: Path) -> str:
    html = (carpeta / "index.html").read_text(encoding="utf-8")
    css = (carpeta / "estilos.css").read_text(encoding="utf-8").rstrip("\n")
    js = (carpeta / "app.js").read_text(encoding="utf-8").rstrip("\n")
    return html.replace("/*__ESTILOS__*/", css, 1).replace("/*__CODIGO__*/", js, 1)


def dashboard() -> str:
    return ensamblar(RAIZ / "plantillas" / "dashboard")


if __name__ == "__main__":
    destino = RAIZ / "plantillas" / "dashboard.html"
    destino.write_text(dashboard(), encoding="utf-8")
    print(f"→ {destino}")
