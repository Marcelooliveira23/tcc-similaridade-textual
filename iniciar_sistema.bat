@echo off
setlocal

cd /d "%~dp0"

set "PY_CMD="
where py >nul 2>&1
if %errorlevel%==0 (
	set "PY_CMD=py"
) else (
	where python >nul 2>&1
	if %errorlevel%==0 (
		set "PY_CMD=python"
	) else (
		echo Python nao encontrado no PATH.
		echo Instale Python ou ajuste as variaveis de ambiente e tente novamente.
		pause
		exit /b 1
	)
)

echo Iniciando Sistema TCC - Similaridade Textual...
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:5000'"
%PY_CMD% -m flask --app src.main run --debug

if errorlevel 1 (
	echo.
	echo Nao foi possivel iniciar o servidor Flask.
	pause
)

endlocal