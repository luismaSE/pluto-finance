#!/usr/bin/env bash
# Instalación de Mi cartera (Linux y macOS). Uso: ./instalar.sh
set -euo pipefail
cd "$(dirname "$0")"
echo "== Mi cartera: instalación =="

PY=""
for c in python3.13 python3.12 python3.11 python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Necesitás Python 3.11 o más nuevo (python.org, o el gestor de paquetes de tu sistema)."; exit 1
fi
echo "→ Python: $($PY --version)"

[ -d .venv ] || "$PY" -m venv .venv
echo "→ Instalando dependencias (puede tardar unos minutos)…"
.venv/bin/python -m pip install --upgrade pip -q
.venv/bin/python -m pip install -q -r requirements-escritorio.txt

read -r -p "¿Instalar el navegador para la descarga asistida de resúmenes? (~150 MB) [S/n] " r || r=""
if [[ ! "$r" =~ ^[nN] ]]; then .venv/bin/python -m playwright install chromium; fi

[ -f config.toml ] || echo "→ La primera vez que abras la app te guía un asistente de configuración."

.venv/bin/python - <<'PY'
import configuracion as c
ok, d = c.llavero_disponible()
print("→ Llavero del sistema:", f"OK ({d})" if ok else f"NO DISPONIBLE: {d}")
if not ok:
    print("  Sin llavero, las claves no se pueden guardar. En Linux instalá gnome-keyring o kwallet.")
PY
command -v claude >/dev/null 2>&1 || echo "→ Aviso: no encontré Claude Code. Podés elegir otro proveedor de IA en la app (API de Anthropic, OpenAI u Ollama)."

if [ "$(uname)" = "Linux" ]; then ./escritorio/acceso_directo.sh; fi
echo
echo "Listo. Abrí la app con ./iniciar.sh (o buscá \"Mi cartera\" en el menú de aplicaciones)."
