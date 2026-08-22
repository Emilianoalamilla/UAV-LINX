# src/main.py
import sys
import os
import ctypes
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QListWidget, QStackedWidget, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from parsers.data_loader import DataLoader
from modules.module_aerodinamica import AerodinamicaWidget
from modules.module_velocidades import VelocidadesWidget
from modules.module_atmosfera import AtmosferaWidget
from modules.module_potencia import PotenciaWidget
from modules.module_geometria_3d import Geometria3DWidget
from modules.module_paneles import SizingWidget
from modules.module_rendimiento_avanzado import RendimientoAvanzadoWidget
from modules.module_mision_perfil import MisionPerfilWidget
from modules.module_vlm_aerodinamica import VLMAerodinamicaWidget
from modules.module_export_simulink import SimulinkExportWidget
from modules.module_estabilidad import EstabilidadWidget

class HaledroneApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HALE Solar UAV - Dashboard de Ingeniería")
        self.resize(1200, 800)
        
        # Set App Icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.data_loader = DataLoader()
        # Cargar datos automáticamente sin botones
        self.data_loader.cargar_atmosfera()
        self.data_loader.cargar_aerodinamica()
        
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        # Configurar fuente profesional (Roboto o Segoe UI)
        font = QFont("Segoe UI", 10)
        QApplication.setFont(font)
        
        # Widget Central y Layout Principal Horizontal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Panel Lateral (Sidebar) ---
        sidebar_panel = QWidget()
        sidebar_panel.setFixedWidth(250)
        sidebar_panel.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar_panel)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(10)
        
        # Título del Sidebar
        title_label = QLabel("HALE UAV\nSizing & Performance")
        title_label.setObjectName("AppTitle")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Lista de Selección
        self.sidebar_list = QListWidget()
        self.sidebar_list.setObjectName("SidebarList")
        self.sidebar_list.addItem("1. Condiciones Ambientales (Atmósfera)")
        self.sidebar_list.addItem("2. Análisis Aerodinámico (Polares)")
        self.sidebar_list.addItem("3. Envolvente de Vuelo (Velocidades)")
        self.sidebar_list.addItem("4. Balance de Potencia (Propulsión)")
        self.sidebar_list.addItem("5. Diseño Geométrico 3D (BWB Sizing)")
        self.sidebar_list.addItem("6. Superficies y Rendimiento Avanzado")
        self.sidebar_list.addItem("7. Optimización Multidisciplinaria (MDO)")
        self.sidebar_list.addItem("8. Perfil de Misión y Autonomía 24h")
        self.sidebar_list.addItem("9. Aerodinámica Computacional (VLM)")
        self.sidebar_list.addItem("10. Exportación a Simulink 6-DOF")
        self.sidebar_list.addItem("11. Análisis de Estabilidad (H + V)")
        
        self.sidebar_list.currentRowChanged.connect(self.change_page)
        
        sidebar_layout.addWidget(title_label)
        sidebar_layout.addSpacing(20)
        sidebar_layout.addWidget(self.sidebar_list)
        
        # --- Área Principal (Contenido) ---
        self.stacked_widget = QStackedWidget()
        
        # Instanciar módulos
        self.tab_atmosfera = AtmosferaWidget(self.data_loader)
        self.tab_aerodinamica = AerodinamicaWidget(self.data_loader)
        self.tab_velocidades = VelocidadesWidget(self.data_loader)
        self.tab_potencia = PotenciaWidget(self.data_loader)
        self.tab_geometria = Geometria3DWidget(self.data_loader)
        self.tab_rendimiento = RendimientoAvanzadoWidget(self.data_loader)
        self.tab_paneles = SizingWidget(self.data_loader)
        self.tab_mision = MisionPerfilWidget(self.data_loader)
        self.tab_vlm = VLMAerodinamicaWidget(self.data_loader)
        self.tab_simulink = SimulinkExportWidget(self.data_loader)
        self.tab_estabilidad = EstabilidadWidget(self.data_loader)
        
        self.stacked_widget.addWidget(self.tab_atmosfera)
        self.stacked_widget.addWidget(self.tab_aerodinamica)
        self.stacked_widget.addWidget(self.tab_velocidades)
        self.stacked_widget.addWidget(self.tab_potencia)
        self.stacked_widget.addWidget(self.tab_geometria)
        self.stacked_widget.addWidget(self.tab_rendimiento)
        self.stacked_widget.addWidget(self.tab_paneles)
        self.stacked_widget.addWidget(self.tab_mision)
        self.stacked_widget.addWidget(self.tab_vlm)
        self.stacked_widget.addWidget(self.tab_simulink)
        self.stacked_widget.addWidget(self.tab_estabilidad)
        
        main_layout.addWidget(sidebar_panel)
        main_layout.addWidget(self.stacked_widget)
        
        # Seleccionar primera opción por defecto
        self.sidebar_list.setCurrentRow(0)
        
    def change_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        
    def apply_styles(self):
        # Tema profesional y oscuro/elegante (Dark/Sleek Theme)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ECEFF1;
            }
            #Sidebar {
                background-color: #2C3E50;
            }
            #AppTitle {
                font-size: 18px;
                font-weight: bold;
                color: #ECF0F1;
                margin-bottom: 20px;
            }
            #SidebarList {
                background-color: #2C3E50;
                color: #BDC3C7;
                border: none;
                font-size: 14px;
                outline: 0;
            }
            #SidebarList::item {
                padding: 12px;
                border-radius: 6px;
                margin-bottom: 5px;
            }
            #SidebarList::item:selected {
                background-color: #34495E;
                color: #FFFFFF;
                font-weight: bold;
                border-left: 4px solid #3498DB;
            }
            #SidebarList::item:hover:!selected {
                background-color: #34495E;
                color: #ECF0F1;
            }
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QTableWidget {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #34495E;
                color: white;
                padding: 5px;
                font-weight: bold;
                border: none;
            }
        """)

if __name__ == "__main__":
    # Fix para que Windows muestre el ícono en la barra de tareas (Taskbar)
    import sys
    if sys.platform == 'win32':
        myappid = 'hale.solar.uav.dashboard.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = HaledroneApp()
    window.show()
    sys.exit(app.exec())
