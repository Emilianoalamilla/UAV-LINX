# module_geometria_3d.py
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from core.globals import UAVConstants

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import mpl_toolkits.mplot3d.art3d as art3d
import mplcursors

class Geometria3DWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.setup_ui()
        self.procesar_geometria()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Renderizando Ala Recta 3D con Fuselaje y Empenaje...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        self.main_layout.addWidget(self.status_label)
        
        # Canvas 3D
        self.figure = Figure(figsize=(10, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.canvas)
        
    def naca4_thickness(self, x_c, t=0.12):
        """Grosor para un perfil NACA (simétrico) dado x/c entre 0 y 1"""
        return 5 * t * (0.2969 * np.sqrt(x_c) - 0.1260 * x_c - 0.3516 * x_c**2 + 0.2843 * x_c**3 - 0.1015 * x_c**4)

    def procesar_geometria(self):
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111, projection='3d')
            
            # --- PARÁMETROS FÍSICOS (Ala Recta Constante) ---
            b = UAVConstants.WINGSPAN_M if hasattr(UAVConstants, 'WINGSPAN_M') else 15.5
            S = UAVConstants.SURFACE_AREA
            c_const = S / b # Cuerda constante ~0.95m
            dihedral_deg = 5.0
            dihedral_rad = np.radians(dihedral_deg)
            
            y_pts = np.linspace(-b/2, b/2, 40)
            x_pts = np.linspace(0, 1, 30) # x/c
            
            Y, X_c = np.meshgrid(y_pts, x_pts)
            
            # Cuerda constante
            C_local = np.ones_like(Y) * c_const
            
            # Ala Recta (Leading Edge en X=0)
            X_LE = np.zeros_like(Y)
            X = X_LE + X_c * C_local
            
            # Coordenadas Z reales (Diedro + Grosor aerodinámico constante)
            T_local = 0.12 # Grosor 12%
            
            Z_up = np.abs(Y) * np.sin(dihedral_rad) + self.naca4_thickness(X_c, T_local) * C_local
            Z_down = np.abs(Y) * np.sin(dihedral_rad) - self.naca4_thickness(X_c, T_local) * C_local
            
            # Dibujar Superficie Superior (Azul Cyan) e Inferior
            ax.plot_surface(X, Y, Z_up, color='#0ea5e9', alpha=0.8, edgecolor='#0284c7', linewidth=0.2)
            ax.plot_surface(X, Y, Z_down, color='#94a3b8', alpha=0.8, edgecolor='#64748b', linewidth=0.2)
            
            # --- SUPERFICIES DE CONTROL ---
            # Flaps: 10% a 65% de la envergadura (y_min=0.775, y_max=5.0)
            flap_y_min = b/2 * 0.10
            flap_y_max = b/2 * 0.65
            mask_flaps = (np.abs(Y) >= flap_y_min) & (np.abs(Y) <= flap_y_max) & (X_c >= 0.75)
            
            # Alerones: 65% a 95% de la envergadura (y_min=5.0, y_max=7.36)
            ail_y_min = b/2 * 0.65
            ail_y_max = b/2 * 0.95
            mask_ailerons = (np.abs(Y) >= ail_y_min) & (np.abs(Y) <= ail_y_max) & (X_c >= 0.78)
            
            Z_flaps = np.where(mask_flaps, Z_up + 0.05, np.nan)
            Z_ail = np.where(mask_ailerons, Z_up + 0.05, np.nan)
            
            ax.plot_surface(X, Y, Z_flaps, color='#10b981', alpha=0.9) # Verde Flaps
            ax.plot_surface(X, Y, Z_ail, color='#ef4444', alpha=0.9)   # Rojo Alerones
            
            # --- FUSELAJE CENTRAL ---
            # Fuselaje removido a petición del usuario

            
            # --- EMPENAJE CONVENCIONAL ---
            # Tail Boom
            tail_arm = 4.5
            boom_start = c_const
            x_boom = np.linspace(boom_start, boom_start + tail_arm, 10)
            y_boom = np.zeros_like(x_boom)
            z_boom = np.zeros_like(x_boom)
            ax.plot(x_boom, y_boom, z_boom, color='#475569', linewidth=4)
            
            # Estabilizador Horizontal (Área ~ 15% de S)
            S_ht = S * 0.15
            ht_span = 3.5
            ht_chord = S_ht / ht_span
            
            x_ht = np.array([x_boom[-1] - ht_chord, x_boom[-1], x_boom[-1], x_boom[-1] - ht_chord])
            y_ht = np.array([-ht_span/2, -ht_span/2, ht_span/2, ht_span/2])
            z_ht = np.array([0, 0, 0, 0])
            ht_poly = art3d.Poly3DCollection([list(zip(x_ht, y_ht, z_ht))], facecolors='#f59e0b', edgecolors='black', alpha=0.8)
            ax.add_collection3d(ht_poly)
            
            # Elevador
            el_chord = ht_chord * 0.25
            x_el = np.array([x_boom[-1] - el_chord, x_boom[-1], x_boom[-1], x_boom[-1] - el_chord])
            el_poly = art3d.Poly3DCollection([list(zip(x_el, y_ht, z_ht))], facecolors='#8b5cf6', edgecolors='black', alpha=0.9)
            ax.add_collection3d(el_poly)
            
            # Estabilizador Vertical (Área ~ 8% de S)
            S_vt = S * 0.08
            vt_span = 1.5
            vt_chord = S_vt / vt_span
            
            x_vt = np.array([x_boom[-1] - vt_chord, x_boom[-1], x_boom[-1], x_boom[-1] - vt_chord*0.5])
            y_vt = np.array([0, 0, 0, 0])
            z_vt = np.array([0, 0, vt_span, vt_span])
            vt_poly = art3d.Poly3DCollection([list(zip(x_vt, y_vt, z_vt))], facecolors='#f59e0b', edgecolors='black', alpha=0.8)
            ax.add_collection3d(vt_poly)
            
            # Timón
            ru_chord = vt_chord * 0.3
            x_ru = np.array([x_boom[-1] - ru_chord, x_boom[-1], x_boom[-1], x_boom[-1] - ru_chord])
            ru_poly = art3d.Poly3DCollection([list(zip(x_ru, y_vt, z_vt))], facecolors='#8b5cf6', edgecolors='black', alpha=0.9)
            ax.add_collection3d(ru_poly)

            # --- AJUSTES DE VISTA ---
            max_range = np.array([X.max()-X.min(), Y.max()-Y.min(), 5.0]).max() / 2.0
            mid_x = (X.max()+X.min()) * 0.5
            mid_y = (Y.max()+Y.min()) * 0.5
            mid_z = 0
            
            ax.set_xlim(mid_x - max_range, mid_x + max_range)
            ax.set_ylim(mid_y - max_range, mid_y + max_range)
            ax.set_zlim(mid_z - max_range*0.3, mid_z + max_range*0.3)
            
            ax.set_title("Renderizado 3D: Ala Recta + Empenaje Convencional", fontsize=14, fontweight='bold', color='#1e293b')
            ax.set_xlabel('Eje X (Cuerda) [m]')
            ax.set_ylabel('Envergadura Y [m]')
            ax.set_zlabel('Altura Z [m]')
            
            # Leyenda
            from matplotlib.lines import Line2D
            custom_lines = [
                Line2D([0], [0], color='#0ea5e9', lw=4),
                Line2D([0], [0], color='#10b981', lw=4),
                Line2D([0], [0], color='#ef4444', lw=4),
                Line2D([0], [0], color='#f59e0b', lw=4)
            ]
            ax.legend(custom_lines, ['Ala Recta', 'Flaps', 'Alerones', 'Empenaje'])
            
            ax.view_init(elev=25, azim=-125)
            self.figure.tight_layout()
            self.canvas.draw()
            
            self.status_label.setText(f"Modelo 3D Generado: Envergadura={b}m, Cuerda={c_const:.2f}m, S_HT={S_ht:.2f}m², S_VT={S_vt:.2f}m²")
            self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            self.status_label.setText(f"Error generando Modelo 3D: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.figure.tight_layout()
        self.canvas.draw_idle()
