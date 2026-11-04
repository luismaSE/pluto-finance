"""Genera plantillas/fuentes.css con las tipografías de Pluto embebidas (sin internet).

Bricolage Grotesque (títulos), IBM Plex Sans (texto) e IBM Plex Mono (cifras), solo el
subconjunto latino. Las tres tienen licencia SIL Open Font License 1.1.
Uso: python marca/generar_fuentes.py
"""
import base64
import re
from pathlib import Path

import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
URL = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800"
       "&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap")
DESTINO = Path(__file__).resolve().parent.parent / "plantillas" / "fuentes.css"


def main():
    css = requests.get(URL, headers=UA, timeout=30).text
    archivos = {}   # (familia, url) -> [pesos]   (las fuentes variables comparten archivo)
    for subset, cuerpo in re.findall(r"/\* ([\w-]+) \*/\s*@font-face \{(.*?)\}", css, re.S):
        if subset != "latin":
            continue
        fam = re.search(r"font-family: '([^']+)'", cuerpo).group(1)
        peso = int(re.search(r"font-weight: (\d+)", cuerpo).group(1))
        src = re.search(r"url\((https://[^)]+)\)", cuerpo).group(1)
        archivos.setdefault((fam, src), []).append(peso)
    lineas = ["/* Tipografías de Pluto (SIL Open Font License 1.1). Generado por marca/generar_fuentes.py: no editar a mano. */"]
    for (fam, src), pesos in archivos.items():
        datos = requests.get(src, headers=UA, timeout=30).content
        rango = f"{min(pesos)} {max(pesos)}" if len(pesos) > 1 else str(pesos[0])
        b64 = base64.b64encode(datos).decode()
        lineas.append(f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{rango};font-display:swap;"
                      f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
        print(f"{fam} {rango}: {len(datos) // 1024} KB")
    DESTINO.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"→ {DESTINO} ({DESTINO.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
