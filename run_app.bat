@echo off
echo Iniciando HALE UAV Sizing App con Entorno Virtual de Python 3.12...
echo.

if not exist ".venv_312\Scripts\python.exe" (
    echo [ERROR] No se encuentra el entorno virtual .venv_312
    echo Por favor solicita a Antigravity que lo reinstale.
    pause
    exit /b 1
)

echo [OK] Entorno virtual detectado. Ejecutando src\main.py...
.\.venv_312\Scripts\python src\main.py
pause
