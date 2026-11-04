@echo off
rem Instalacion de Pluto (Windows). Doble clic para ejecutar.
cd /d "%~dp0"
echo == Pluto: instalacion ==
set PY=python
where py >nul 2>nul && set PY=py -3
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>nul
if errorlevel 1 (
  echo Necesitas Python 3.11 o mas nuevo. Instalalo desde python.org marcando "Add Python to PATH".
  pause
  exit /b 1
)
if not exist .venv %PY% -m venv .venv
echo Instalando dependencias, puede tardar unos minutos...
.venv\Scripts\python -m pip install --upgrade pip -q
.venv\Scripts\python -m pip install -q -r requirements-escritorio.txt
choice /m "Instalar el navegador para la descarga asistida de resumenes (~150 MB)"
if errorlevel 2 goto acceso
.venv\Scripts\python -m playwright install chromium
:acceso
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Pluto.lnk'); $s.IconLocation='%CD%\marca\icono.ico'; $s.TargetPath='%CD%\.venv\Scripts\pythonw.exe'; $s.Arguments='\"%CD%\app.py\"'; $s.WorkingDirectory='%CD%'; $s.Save()"
echo.
echo Listo. Se creo el acceso directo "Pluto" en el escritorio (o usa iniciar.bat).
pause
