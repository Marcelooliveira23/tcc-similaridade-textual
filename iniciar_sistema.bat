@echo off
title Sistema TCC - Similaridade Textual
color 0A
cd /d "C:\Users\mrced\OneDrive\Documents\TCC"

echo ================================================
echo   SISTEMA DE COMPARACAO DE SIMILARIDADE TEXTUAL
echo   TCC - Engenharia de Software - UNINTER
echo ================================================
echo.
echo Iniciando servidor Flask...
echo Acesse: http://localhost:5000
echo.
echo Pressione Ctrl+C para encerrar.
echo.

start "" http://localhost:5000
python -m flask --app src.main run --debug

pause
