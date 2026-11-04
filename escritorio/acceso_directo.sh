#!/usr/bin/env bash
# Crea el acceso directo "Pluto" en el menú de aplicaciones (Linux).
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
APPS="$HOME/.local/share/applications"
ICONOS="$HOME/.local/share/icons"
mkdir -p "$APPS" "$ICONOS"
cp "$RAIZ/marca/icono.svg" "$ICONOS/pluto.svg"
# Reemplaza el acceso de versiones anteriores ("Mi cartera")
rm -f "$APPS/mi-cartera.desktop" "$ICONOS/mi-cartera.svg"
cat > "$APPS/pluto.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=Pluto
Comment=Tus bancos, billeteras y brokers en un solo lugar
Exec="$RAIZ/iniciar.sh"
Path=$RAIZ
Icon=$ICONOS/pluto.svg
Terminal=false
Categories=Office;Finance;
StartupWMClass=Pluto
DESK
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" >/dev/null 2>&1 || true
echo "Listo: buscá 'Pluto' en el menú de aplicaciones."
