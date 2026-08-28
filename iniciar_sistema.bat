@echo off
setlocal

cd /d "%~dp0"

echo Iniciando Sistema TCC - Similaridade Textual...
start "" cmd /k "cd /d \"%~dp0\" && python -m flask --app src.main run --debug"
start "" "http://127.0.0.1:5000"

endlocal