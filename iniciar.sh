#!/usr/bin/env bash
# Abre la app de escritorio. Uso: ./iniciar.sh
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { echo "Primero corré ./instalar.sh"; exit 1; }
exec .venv/bin/python app.py "$@"
