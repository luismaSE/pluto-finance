#!/usr/bin/env bash
# Genera la clave de firma del APK y la carga como secrets en GitHub (una sola vez).
# Con la clave propia, cada versión nueva se instala encima de la anterior sin perder la configuración.
#
# Requisitos: keytool (viene con Java) y, para cargar los secrets solo, la CLI de GitHub (gh) logueada.
# Uso: ./android/generar_clave.sh [usuario/repo]
set -euo pipefail
REPO="${1:-$(git config --get remote.origin.url | sed -E 's#.*github.com[:/](.+/[^.]+)(\.git)?$#\1#')}"
DEST="$HOME/.pluto/pluto-release.jks"
ALIAS="pluto"
mkdir -p "$(dirname "$DEST")"; chmod 700 "$(dirname "$DEST")"

if [ -f "$DEST" ]; then
  echo "Ya existe $DEST: uso esa clave (no la borres: sin ella no se puede actualizar la app)."
else
  command -v keytool >/dev/null || { echo "Falta keytool: instalá Java (en Arch: sudo pacman -S jdk-openjdk)."; exit 1; }
  read -r -s -p "Contraseña para la clave (mínimo 6 caracteres, guardala bien): " PASS; echo
  read -r -s -p "Repetila: " PASS2; echo
  [ "$PASS" = "$PASS2" ] || { echo "No coinciden."; exit 1; }
  keytool -genkeypair -v -keystore "$DEST" -alias "$ALIAS" -keyalg RSA -keysize 4096 -validity 10000 \
    -storepass "$PASS" -keypass "$PASS" -dname "CN=Pluto, O=Pluto, C=AR" >/dev/null
  chmod 600 "$DEST"
  echo "✓ Clave creada en $DEST. Hacé una copia de seguridad en un lugar seguro."
fi

if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
  [ -n "${PASS:-}" ] || { read -r -s -p "Contraseña de la clave: " PASS; echo; }
  echo "Cargando los secrets en $REPO…"
  base64 -w0 "$DEST" | gh secret set CARTERA_KEYSTORE_BASE64 --repo "$REPO"
  printf %s "$PASS" | gh secret set CARTERA_KEYSTORE_PASSWORD --repo "$REPO"
  printf %s "$ALIAS" | gh secret set CARTERA_KEY_ALIAS --repo "$REPO"
  printf %s "$PASS" | gh secret set CARTERA_KEY_PASSWORD --repo "$REPO"
  echo "✓ Listo. Los próximos APK salen firmados con tu clave."
  echo "  Ojo: la primera vez hay que desinstalar la app del celular (cambia la firma); después ya no."
else
  echo
  echo "No encontré la CLI de GitHub logueada. Cargá estos 4 secrets a mano en"
  echo "GitHub → $REPO → Settings → Secrets and variables → Actions → New repository secret:"
  echo "  CARTERA_KEYSTORE_BASE64  = el resultado de:  base64 -w0 $DEST"
  echo "  CARTERA_KEYSTORE_PASSWORD = tu contraseña"
  echo "  CARTERA_KEY_ALIAS         = $ALIAS"
  echo "  CARTERA_KEY_PASSWORD      = tu contraseña"
fi
