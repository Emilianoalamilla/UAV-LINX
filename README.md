# HALE UAV Simulator

Simulador y herramienta de dimensionamiento aerodinámico para vehículos aéreos no tripulados (UAV) tipo HALE (High Altitude Long Endurance) impulsados por energía solar.

## Características
*   **Aerodinámica Computacional (VLM):** Análisis del Vortex Lattice Method.
*   **Análisis de Estabilidad (H + V):** Estabilidad estática y dinámica longitudinal y direccional.
*   **Generador de Reportes LaTeX:** Reportes automatizados de resultados.
*   **Exportación a Simulink:** Modelo de 6-DOF (Grados de Libertad).
*   **Perfiles de Misión:** Cálculo de autonomía y requerimientos de potencia solar.

## Requisitos
*   Python 3.12+
*   Librerías detalladas en `requirements.txt` (PySide6, pandas, matplotlib, scipy, etc.)

## Ejecución Local
1.  Clona este repositorio.
2.  Activa o crea un entorno virtual e instala los requerimientos: `pip install -r requirements.txt`.
3.  Ejecuta la interfaz: `python src/main.py`.
