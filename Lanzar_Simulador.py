import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

print("==================================================")
print(" HALE UAV - LANZADOR DIRECTO DE SIMULACION 3D")
print("==================================================")
print("\nIniciando secuencia de inyeccion a MATLAB y FlightGear...\n")

try:
    from PySide6.QtWidgets import QApplication
    from modules.module_export_simulink import SimulinkExportWidget
    
    # Crear aplicacion de consola sin ventana para instanciar el Widget
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        
    class DummyConsole:
        def append(self, text):
            print(text)
            
    # Instanciar el modulo de exportacion directamente
    widget = SimulinkExportWidget(None)
    widget.console = DummyConsole() # Redirigir consola de la UI a la terminal
    
    # Ejecutar la inyeccion
    widget.inject_via_api()
    
except Exception as e:
    import traceback
    print(f"\nERROR FATAL: {str(e)}")
    traceback.print_exc()
    print("\nAsegurate de que MATLAB este abierto y ejecutaste 'matlab.engine.shareEngine'")
