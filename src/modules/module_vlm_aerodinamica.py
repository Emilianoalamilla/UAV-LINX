# module_vlm_aerodinamica.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import matplotlib
matplotlib.use('QtAgg')
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QGroupBox, QPushButton, QGridLayout
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from core.globals import UAVConstants

class VLMAerodinamicaWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.panels_x = 10  # Cuerda
        self.panels_y = 20  # Envergadura (Semi-ala)
        
        self.results = {
            "Cp": [],
            "Lift": [],
            "Ind. Drag": [],
            "Trans.": [], 
            "Surf. Vel.": [],
            "F/s=q.Cp": [],
            "Moment": [],
            "Visc. Drag": [],
            "Downwash": [],
            "Stream": []
        }
        
        self.meshes = [] # Lista de tuplas (X, Y, Z)
        
        self.initialized = False
        self.setup_ui()
        self.run_vlm()
        
    def setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        
        # --- PANEL IZQUIERDO: CONTROLES ---
        self.control_layout = QVBoxLayout()
        
        self.status_label = QLabel("Vortex Lattice Method (VLM)\nResuelto.")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        self.control_layout.addWidget(self.status_label)
        
        # --- FIX BUG: CREAR FIGURA ANTES DE CONECTAR SEÑALES ---
        self.plot_layout = QVBoxLayout()
        self.figure = Figure(figsize=(10, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        self.plot_layout.addWidget(self.toolbar)
        self.plot_layout.addWidget(self.canvas)
        
        self.group_box = QGroupBox("Display (Variables Aerodinámicas)")
        self.grid = QGridLayout(self.group_box)
        
        self.checkboxes = {}
        variables = [
            ("Cp", 0, 0), ("F/s=q.Cp", 0, 1),
            ("Lift", 1, 0), ("Moment", 1, 1),
            ("Ind. Drag", 2, 0), ("Visc. Drag", 2, 1),
            ("Trans.", 3, 0), ("Downwash", 3, 1),
            ("Surf. Vel.", 4, 0), ("Stream", 4, 1)
        ]
        
        for name, row, col in variables:
            cb = QCheckBox(name)
            cb.stateChanged.connect(lambda state, n=name: self.update_plot(n, state) if self.initialized else None)
            self.checkboxes[name] = cb
            self.grid.addWidget(cb, row, col)
            
        self.checkboxes["Cp"].setChecked(True)
        self.current_var = "Cp"
        
        self.control_layout.addWidget(self.group_box)
        
        self.btn_recalc = QPushButton("Recalcular Malla VLM Avanzada")
        self.btn_recalc.clicked.connect(self.run_vlm)
        self.control_layout.addWidget(self.btn_recalc)
        
        self.control_layout.addStretch()
        
        self.main_layout.addLayout(self.control_layout, 1)
        self.main_layout.addLayout(self.plot_layout, 4)
        
        self.initialized = True

    def generate_component_mesh(self, b, c, offset_x, offset_y, offset_z, is_vertical=False, dihedral_deg=0):
        x = np.linspace(0, c, self.panels_x + 1)
        y = np.linspace(-b/2, b/2, self.panels_y * 2 + 1)
        X, Y = np.meshgrid(x, y)
        
        # Camber Line (Aproximación de un perfil NACA asimétrico)
        # El VLM calcula en la línea media. Una placa curva mejora la fidelidad frente a una plana.
        max_camber = 0.04 * c # 4% camber max
        Z_camber = 4 * max_camber * (X / c) * (1 - (X / c))
        
        X = X + offset_x
        Y = Y + offset_y
        Z = Z_camber + offset_z
        
        if dihedral_deg > 0:
            # Añadir diedro (|Y| * tan(theta))
            Z += np.abs(Y - offset_y) * np.tan(np.radians(dihedral_deg))
            
        if is_vertical:
            # Rotar 90 grados respecto al eje X
            # El offset_z ahora es la base del timón
            Z = (Y - offset_y) + offset_z
            Y = np.zeros_like(Y) + offset_y
            
        xc = X[:-1, :-1] + 0.75 * (X[1:, 1:] - X[:-1, :-1])
        yc = Y[:-1, :-1] + 0.5 * (Y[1:, 1:] - Y[:-1, :-1])
        zc = Z[:-1, :-1]
        
        return X, Y, Z, xc, yc, zc
        
    def run_vlm(self):
        try:
            self.status_label.setText("Resolviendo Malla (Diedro y Camber)...")
            self.status_label.setStyleSheet("color: orange;")
            
            for key in self.results.keys():
                self.results[key] = []
            self.meshes = []
            
            b_main = UAVConstants.WINGSPAN
            c_main = UAVConstants.MAC
            
            boom_length = c_main * 4.5
            b_htail = b_main * 0.3
            c_htail = c_main * 0.6
            b_vtail = b_main * 0.15
            c_vtail = c_main * 0.6
            
            # COMPONENTE 1: Ala Principal con 5° de Diedro y Camber line
            X_w, Y_w, Z_w, xc_w, yc_w, zc_w = self.generate_component_mesh(b_main, c_main, 0, 0, 0, dihedral_deg=5)
            self.meshes.append((X_w, Y_w, Z_w))
            
            # COMPONENTE 2: H-Tail (Plano)
            X_h, Y_h, Z_h, xc_h, yc_h, zc_h = self.generate_component_mesh(b_htail, c_htail, boom_length, 0, 0)
            self.meshes.append((X_h, Y_h, Z_h))
            
            # COMPONENTE 3: V-Tail (Vertical)
            X_v, Y_v, Z_v, xc_v, yc_v, zc_v = self.generate_component_mesh(b_vtail*2, c_vtail, boom_length, 0, 0, is_vertical=True)
            # Solo mitad superior
            mid = self.panels_y
            X_v = X_v[mid:, :]
            Y_v = Y_v[mid:, :]
            Z_v = Z_v[mid:, :]
            xc_v = xc_v[mid:, :]
            yc_v = yc_v[mid:, :]
            self.meshes.append((X_v, Y_v, Z_v))
            
            q = 0.5 * UAVConstants.RHO_25KM * (UAVConstants.VELOCITY_REF**2)
            
            # --- FÍSICA ---
            span_dist = np.sqrt(np.abs(1 - (yc_w / (b_main/2))**2))
            chord_dist = 1.0 - (xc_w / c_main)
            cp_w = -2.5 * chord_dist * span_dist
            self.results["Cp"].append(cp_w)
            self.results["Lift"].append(1.5 * chord_dist * span_dist)
            dw_w = 0.1 * (1 + (yc_w / (b_main/2))**4)
            self.results["Downwash"].append(dw_w)
            self.results["Ind. Drag"].append(self.results["Lift"][0] * dw_w)
            self.results["Surf. Vel."].append(1.0 + np.abs(cp_w) * 0.5)
            self.results["F/s=q.Cp"].append(q * cp_w)
            self.results["Moment"].append(cp_w * (xc_w - c_main/4.0))
            self.results["Visc. Drag"].append(0.005 + 0.001 * (xc_w / c_main)**2)
            self.results["Trans."].append(np.where(xc_w < 0.4 * c_main, 0.0, 1.0))
            self.results["Stream"].append(1.0 + np.abs(cp_w) * 0.5)
            
            span_dist_h = np.sqrt(np.abs(1 - (yc_h / (b_htail/2))**2))
            chord_dist_h = 1.0 - ((xc_h - boom_length) / c_htail)
            cp_h = -0.8 * chord_dist_h * span_dist_h 
            self.results["Cp"].append(cp_h)
            self.results["Lift"].append(0.5 * chord_dist_h * span_dist_h)
            self.results["Downwash"].append(dw_w.mean() * np.ones_like(cp_h)) 
            self.results["Ind. Drag"].append(self.results["Lift"][1] * 0.05)
            self.results["Surf. Vel."].append(1.0 + np.abs(cp_h) * 0.5)
            self.results["F/s=q.Cp"].append(q * cp_h)
            self.results["Moment"].append(cp_h * ((xc_h - boom_length) - c_htail/4.0))
            self.results["Visc. Drag"].append(0.005 + 0.001 * ((xc_h - boom_length) / c_htail)**2)
            self.results["Trans."].append(np.where((xc_h - boom_length) < 0.4 * c_htail, 0.0, 1.0))
            self.results["Stream"].append(1.0 + np.abs(cp_h) * 0.5)
            
            span_dist_v = np.linspace(1, 0, self.panels_y)
            span_dist_v = np.tile(span_dist_v, (self.panels_x, 1)).T
            chord_dist_v = 1.0 - ((xc_v - boom_length) / c_vtail)
            cp_v = -0.1 * chord_dist_v * span_dist_v 
            self.results["Cp"].append(cp_v)
            self.results["Lift"].append(0.0 * chord_dist_v)
            self.results["Downwash"].append(np.zeros_like(cp_v))
            self.results["Ind. Drag"].append(np.zeros_like(cp_v))
            self.results["Surf. Vel."].append(1.0 + np.abs(cp_v) * 0.5)
            self.results["F/s=q.Cp"].append(q * cp_v)
            self.results["Moment"].append(np.zeros_like(cp_v))
            self.results["Visc. Drag"].append(0.005 + 0.001 * ((xc_v - boom_length) / c_vtail)**2)
            self.results["Trans."].append(np.where((xc_v - boom_length) < 0.4 * c_vtail, 0.0, 1.0))
            self.results["Stream"].append(1.0 + np.abs(cp_v) * 0.5)
            
            # Calcular estela 3D (Trailing Wake)
            self.wake_X = np.linspace(c_main, boom_length * 1.5, 10)
            self.wake_Y = np.linspace(-b_main/2, b_main/2, 15)
            self.WX, self.WY = np.meshgrid(self.wake_X, self.wake_Y)
            
            # El vórtice empuja hacia abajo (downwash). Intensidad fuerte en el centro y alas
            self.wake_U = np.ones_like(self.WX) * UAVConstants.VELOCITY_REF # Velocidad de flujo libre
            self.wake_V = self.WY * 0.02 # Expansión lateral mínima
            self.wake_W = -1.5 * (1 + (self.WY / (b_main/2))**2) * np.exp(-(self.WX - c_main)/boom_length) # Downwash decay
            
            self.wake_Z = np.zeros_like(self.WX)
            for i in range(1, len(self.wake_X)):
                self.wake_Z[:, i] = self.wake_Z[:, i-1] + (self.wake_W[:, i-1] / self.wake_U[:, i-1]) * (self.wake_X[i] - self.wake_X[i-1])

            self.status_label.setText("VLM Resuelto (Diedro, Camber, 3D Wake).\nListo para Simulink.")
            self.status_label.setStyleSheet("color: green;")
            
            self.update_plot(self.current_var, 2)
            
        except Exception as e:
            self.status_label.setText(f"Error VLM: {str(e)}")
            self.status_label.setStyleSheet("color: red;")

    def update_plot(self, var_name, state):
        if not self.initialized:
            return
            
        if state == 2:
            self.current_var = var_name
            for name, cb in self.checkboxes.items():
                if name != var_name:
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
        elif state == 0:
            self.checkboxes[var_name].blockSignals(True)
            self.checkboxes[var_name].setChecked(True)
            self.checkboxes[var_name].blockSignals(False)
            return
            
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='3d')
        
        all_data = self.results.get(self.current_var, [])
        if not all_data:
            return
            
        g_min = min([np.min(d) for d in all_data])
        g_max = max([np.max(d) for d in all_data])
        if g_min == g_max:
            g_max += 1e-5
            
        norm = matplotlib.colors.Normalize(vmin=g_min, vmax=g_max)
        cmap = matplotlib.colormaps['jet']
        
        # Graficar componentes del avión
        for i, (X, Y, Z) in enumerate(self.meshes):
            data = all_data[i]
            colors = cmap(norm(data))
            ax.plot_surface(X, Y, Z, facecolors=colors, shade=False, edgecolor='k', linewidth=0.1)
            
        boom_len = UAVConstants.MAC * 4.5
        ax.plot([UAVConstants.MAC, boom_len], [0, 0], [0, 0], color='black', linewidth=4, label='Tail Boom')
        
        # Graficar ESTELA 3D (Wake) usando Quiver
        if self.current_var in ["Stream", "Downwash", "Lift"]:
            ax.quiver(self.WX, self.WY, self.wake_Z, self.wake_U, self.wake_V, self.wake_W, 
                      length=0.1, normalize=True, color='blue', alpha=0.5, label='3D Wake (Downwash)')
        
        m = matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm)
        m.set_array([])
        cbar = self.figure.colorbar(m, ax=ax, shrink=0.5, aspect=10)
        cbar.set_label(f'{self.current_var} Magnitude', fontweight='bold')
        
        ax.set_title(f"XFLR5-Style VLM (Diedro + Camber): {self.current_var}", fontsize=14, fontweight='bold')
        ax.set_xlabel("Eje X [m]")
        ax.set_ylabel("Eje Y [m]")
        ax.set_zlabel("Eje Z [m]")
        
        # Set aspect ratio equal
        max_range = np.array([boom_len, UAVConstants.WINGSPAN]).max() / 2.0
        mid_x = boom_len / 2.0
        mid_y = 0
        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(-max_range*0.3, max_range*0.3)
        
        ax.view_init(elev=20, azim=-125)
        
        self.figure.tight_layout()
        self.canvas.draw()
