@echo off
rem Abre la app de escritorio de Mi cartera.
cd /d "%~dp0"
if not exist .venv\Scripts\pythonw.exe (
  echo Primero ejecuta instalar.bat
  pause
  exit /b 1
)
start "" .venv\Scripts\pythonw.exe app.py
