# module_sizing_fisico.py
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from core.globals import UAVConstants

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
import mplcursors

class SizingFisicoWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.setup_ui()
        self.procesar_sizing()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Info Panel
        self.status_label = QLabel("Calculando Dimensionamiento Físico...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        self.main_layout.addWidget(self.status_label)
        
        # Gráfica
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.canvas)
        
    def procesar_sizing(self):
        try:
            b = UAVConstants.WINGSPAN_M if hasattr(UAVConstants, 'WINGSPAN_M') else 15.5
            S = UAVConstants.SURFACE_AREA
            W = UAVConstants.WEIGHT_N
            mass = W / 9.81
            chord = S / b
            dihedral_deg = 5.0
            dihedral_rad = np.radians(dihedral_deg)
            
            self.figure.clear()
            ax1 = self.figure.add_subplot(211)
            ax2 = self.figure.add_subplot(212)
            
            # --- Vista Superior (Planta) ---
            # Ala rectangular simplificada
            y_wing = [-b/2, b/2, b/2, -b/2]
            x_wing = [-chord/2, -chord/2, chord/2, chord/2]
            
            wing_poly = Polygon(xy=list(zip(y_wing, x_wing)), closed=True, facecolor='#3498db', edgecolor='#2980b9', alpha=0.7, linewidth=2)
            ax1.add_patch(wing_poly)
            
            # Fuselaje simplificado (cilindro)
            fuse_length = chord * 3
            fuse_width = chord * 0.4
            y_fuse = [-fuse_width/2, fuse_width/2, fuse_width/2, -fuse_width/2]
            x_fuse = [-fuse_length*0.3, -fuse_length*0.3, fuse_length*0.7, fuse_length*0.7]
            fuse_poly = Polygon(xy=list(zip(y_fuse, x_fuse)), closed=True, facecolor='#95a5a6', edgecolor='#7f8c8d', alpha=0.9)
            ax1.add_patch(fuse_poly)
            
            # Empenaje horizontal (Cola)
            htail_span = b * 0.25
            htail_chord = chord * 0.6
            y_ht = [-htail_span/2, htail_span/2, htail_span/2, -htail_span/2]
            x_ht = [fuse_length*0.6, fuse_length*0.6, fuse_length*0.6+htail_chord, fuse_length*0.6+htail_chord]
            ht_poly = Polygon(xy=list(zip(y_ht, x_ht)), closed=True, facecolor='#e74c3c', edgecolor='#c0392b', alpha=0.7)
            ax1.add_patch(ht_poly)
            
            ax1.set_xlim(-b/2 - 1, b/2 + 1)
            ax1.set_ylim(-fuse_length*0.5, fuse_length*1.2)
            ax1.set_aspect('equal')
            ax1.set_title('Vista en Planta (Top View)', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Envergadura (Y) [m]', fontsize=12)
            ax1.set_ylabel('Eje Longitudinal (X) [m]', fontsize=12)
            ax1.grid(True, linestyle='--', alpha=0.5)
            
            # Anotaciones
            ax1.annotate(f'b = {b} m', xy=(0, chord/2), xytext=(0, chord/2 + 1),
                         ha='center', arrowprops=dict(arrowstyle='->', lw=1.5))
            ax1.annotate(f'c = {chord:.2f} m', xy=(-b/4, 0), xytext=(-b/4, -1.5),
                         ha='center', arrowprops=dict(arrowstyle='->', lw=1.5))
                         
            # --- Vista Frontal (Diedro) ---
            # Centro del fuselaje
            ax2.add_patch(Polygon(xy=[(-fuse_width/2, -fuse_width/2), (fuse_width/2, -fuse_width/2), 
                                      (fuse_width/2, fuse_width/2), (-fuse_width/2, fuse_width/2)],
                                  closed=True, facecolor='#95a5a6', edgecolor='#7f8c8d'))
            
            # Semiala Izquierda
            z_tip = (b/2) * np.sin(dihedral_rad)
            y_tip = (b/2) * np.cos(dihedral_rad)
            wing_thickness = 0.1
            
            y_left = [0, -y_tip, -y_tip, 0]
            z_left = [0, z_tip, z_tip - wing_thickness, -wing_thickness]
            ax2.add_patch(Polygon(xy=list(zip(y_left, z_left)), closed=True, facecolor='#3498db', edgecolor='#2980b9', alpha=0.7))
            
            # Semiala Derecha
            y_right = [0, y_tip, y_tip, 0]
            z_right = [0, z_tip, z_tip - wing_thickness, -wing_thickness]
            ax2.add_patch(Polygon(xy=list(zip(y_right, z_right)), closed=True, facecolor='#3498db', edgecolor='#2980b9', alpha=0.7))
            
            ax2.set_xlim(-b/2 - 1, b/2 + 1)
            ax2.set_ylim(-1, z_tip + 1)
            ax2.set_aspect('equal')
            ax2.set_title('Vista Frontal (Front View)', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Envergadura (Y) [m]', fontsize=12)
            ax2.set_ylabel('Altura (Z) [m]', fontsize=12)
            ax2.grid(True, linestyle='--', alpha=0.5)
            
            # Anotación Diedro
            ax2.annotate(f'Diedro = {dihedral_deg}°', xy=(y_tip/2, z_tip/2), xytext=(y_tip/2, z_tip/2 + 0.5),
                         ha='center', arrowprops=dict(arrowstyle='->', lw=1.5))
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            self.status_label.setText(f"Parámetros: Masa={mass:.1f} kg | S={S} m² | Envergadura={b} m | Cuerda Media={chord:.2f} m")
            self.status_label.setStyleSheet("color: green;")
            
            # Interacción
            mplcursors.cursor(hover=True)
            
        except Exception as e:
            self.status_label.setText(f"Error generando Sizing Físico: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.figure.tight_layout()
        self.canvas.draw_idle()
