#!/usr/bin/env bash
# Crea un acceso directo "Mi cartera" en el menú de aplicaciones (Linux).
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
PY="$RAIZ/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"
mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons"
cat > "$HOME/.local/share/icons/mi-cartera.svg" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#2a78d6"/><rect x="14" y="36" width="9" height="16" rx="2" fill="#fff"/><rect x="28" y="26" width="9" height="26" rx="2" fill="#fff"/><rect x="42" y="14" width="9" height="38" rx="2" fill="#fff"/></svg>
SVG
cat > "$HOME/.local/share/applications/mi-cartera.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=Mi cartera
Comment=IOL, Galicia y Mercado Pago en un solo lugar
Exec="$PY" "$RAIZ/app.py"
Path=$RAIZ
Icon=$HOME/.local/share/icons/mi-cartera.svg
Terminal=false
Categories=Office;Finance;
DESK
echo "Listo: buscá 'Mi cartera' en el menú de aplicaciones."
