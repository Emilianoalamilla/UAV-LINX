@echo off
title HALE UAV - Simulador 3D Directo
color 0A

echo =======================================================
echo   INICIANDO SIMULADOR 3D DIRECTO
echo =======================================================
echo.
echo Recuerda tener MATLAB abierto y ejecutar:
echo matlab.engine.shareEngine
echo.
echo Activando entorno de Python y conectando...
call .venv_312\Scripts\activate.bat
python Lanzar_Simulador.py

echo.
pause
