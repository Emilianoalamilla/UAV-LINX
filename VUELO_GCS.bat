@echo off
title HALE UAV — Ground Control Station
color 0A

echo ═══════════════════════════════════════════════════════
echo   HALE UAV — GROUND CONTROL STATION LAUNCHER
echo ═══════════════════════════════════════════════════════
echo.
echo Requisitos:
echo   - MATLAB R2025a abierto
echo   - matlab.engine.shareEngine ejecutado en MATLAB
echo   - FlightGear 2024.1 instalado (opcional, ventana separada)
echo.
echo Iniciando GCS...
echo.

cd /d "C:\Users\emili\Documents\IPN 2026\2025\linx\linx antigravity\HALE_Simulator_Project"

REM Intentar lanzar directamente en MATLAB
start "" "C:\Program Files\MATLAB\R2025a\bin\matlab.exe" -r "run('HALE_GroundStation.m')"

echo.
echo MATLAB se esta abriendo con el GCS...
echo Si MATLAB ya esta abierto, ejecuta manualmente:
echo   ^> cd 'C:\Users\emili\Documents\IPN 2026\2025\linx\linx antigravity\HALE_Simulator_Project'
echo   ^> HALE_GroundStation
echo.
pause
