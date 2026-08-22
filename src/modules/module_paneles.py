# module_paneles.py (Sizing & Trade-off Optimization)
import numpy as np
import pandas as pd
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget
from PySide6.QtCore import Qt
from core.globals import UAVConstants

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import mplcursors

class SizingWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.setup_ui()
        self.procesar_sizing()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Info Panel
        self.status_label = QLabel("Calculando Mapa de Optimización...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        self.main_layout.addWidget(self.status_label)
        
        # Tab Widget para organizar gráficas
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Tab 1: Mapa de Calor
        self.tab_mapa = QWidget()
        self.layout_mapa = QVBoxLayout(self.tab_mapa)
        self.figure_mapa = Figure(figsize=(10, 6), dpi=100)
        self.canvas_mapa = FigureCanvas(self.figure_mapa)
        self.toolbar_mapa = NavigationToolbar(self.canvas_mapa, self)
        self.layout_mapa.addWidget(self.toolbar_mapa)
        self.layout_mapa.addWidget(self.canvas_mapa)
        self.tabs.addTab(self.tab_mapa, "Mapa de Calor (V vs b)")
        
        # Tab 2: Trade-off 2D
        self.tab_corte = QWidget()
        self.layout_corte = QVBoxLayout(self.tab_corte)
        self.figure_corte = Figure(figsize=(10, 6), dpi=100)
        self.canvas_corte = FigureCanvas(self.figure_corte)
        self.toolbar_corte = NavigationToolbar(self.canvas_corte, self)
        self.layout_corte.addWidget(self.toolbar_corte)
        self.layout_corte.addWidget(self.canvas_corte)
        self.tabs.addTab(self.tab_corte, "Compromiso Estructural (Corte 2D)")
        
    def get_total_weight(self, b, k_wing, w_fixed):
        w_wing = k_wing * (b**1.8)
        return (w_fixed + w_wing) * 9.81 

    def calculate_physics(self, v, b, rho, k_wing, w_fixed, e_oswald, cd_profile, cd_parasitic, eta_total):
        W_real = self.get_total_weight(b, k_wing, w_fixed) 
        S = (b**2) / 18.0 # AR fijo de 18
        
        q = 0.5 * rho * v**2
        CL = W_real / (q * S)
        
        CD_ind = (CL**2) / (np.pi * e_oswald * 18.0)
        CD_tot = cd_profile + cd_parasitic + CD_ind
        
        Drag = q * S * CD_tot
        P_elec = (Drag * v) / eta_total
        
        return P_elec, CL, W_real
        
    def procesar_sizing(self):
        atm_df = self.data_loader.get_atmosfera_data()
        
        try:
            # Obtener rho dinámicamente a la altitud de diseño (25km)
            rho = 0.04008 # Fallback
            if atm_df is not None:
                cols_atm = atm_df.columns.tolist()
                alt_col = next((c for c in cols_atm if 'altitud' in c.lower() or 'h' in c.lower() or '(m)' in c.lower()), cols_atm[0])
                rho_col = next((c for c in cols_atm if 'density' in c.lower() or 'densidad' in c.lower() or 'ρ' in c.lower()), None)
                if rho_col:
                    idx_closest = (atm_df[alt_col] - UAVConstants.MAX_ALTITUDE_M).abs().idxmin()
                    rho = atm_df.loc[idx_closest, rho_col]
            
            # Parámetros aerodinámicos
            e_oswald = 0.9         
            cd_profile = 0.0058    
            cd_parasitic = 0.005   
            eta_total = 0.736      # Eficiencia Global
            
            # Dinámica de Peso Estructural
            b_ref = 15.5
            w_wing_ref = 14.0      
            k_wing = w_wing_ref / (b_ref**1.8) 
            w_fixed = 31.0         # Fuselaje + Bat + Payload
            
            V_design = 39.6        # m/s
            
            # Mallas
            V_vec = np.linspace(25, 55, 100)
            b_vec = np.linspace(10, 22, 100)
            V_grid, b_grid = np.meshgrid(V_vec, b_vec)
            
            P_grid = np.zeros_like(V_grid)
            W_grid_kg = np.zeros_like(V_grid)
            CL_grid = np.zeros_like(V_grid)
            
            for i in range(len(b_vec)):
                for j in range(len(V_vec)):
                    p, cl, w = self.calculate_physics(V_vec[j], b_vec[i], rho, k_wing, w_fixed, e_oswald, cd_profile, cd_parasitic, eta_total)
                    P_grid[i, j] = p
                    W_grid_kg[i, j] = w / 9.81
                    CL_grid[i, j] = cl
                    
            P_masked = np.ma.masked_where(CL_grid > 1.6, P_grid)
            
            # ==========================================
            # FIGURA 1: SUPERFICIE 3D (V vs b vs Potencia)
            # ==========================================
            self.figure_mapa.clear()
            ax1 = self.figure_mapa.add_subplot(111, projection='3d')
            
            # Superficie 3D de Potencia
            surf = ax1.plot_surface(V_grid, b_grid, P_masked, cmap='viridis_r', edgecolor='none', alpha=0.9)
            
            cbar = self.figure_mapa.colorbar(surf, ax=ax1, shrink=0.5, aspect=10, pad=0.1)
            cbar.set_label('Potencia Eléctrica [W]', fontweight='bold')
            
            # Punto de diseño actual
            P_design_new, _, W_design_new = self.calculate_physics(V_design, 15.5, rho, k_wing, w_fixed, e_oswald, cd_profile, cd_parasitic, eta_total)
            ax1.scatter(V_design, 15.5, P_design_new, color='red', s=100, label=f'Diseño Actual ({int(P_design_new)} W)', zorder=10)
            
            ax1.set_title(f'Superficie de Optimización 3D (Altitud: {UAVConstants.MAX_ALTITUDE_M/1000} km)', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Velocidad de Crucero [m/s]', fontsize=12, labelpad=10)
            ax1.set_ylabel('Envergadura Alar [m]', fontsize=12, labelpad=10)
            ax1.set_zlabel('Potencia Requerida [W]', fontsize=12, labelpad=10)
            ax1.legend()
            ax1.view_init(elev=30, azim=-135)
            
            self.figure_mapa.tight_layout()
            self.canvas_mapa.draw()
            
            # ==========================================
            # FIGURA 2: CORTE 2D (TRADE-OFF A 39.6 M/S)
            # ==========================================
            self.figure_corte.clear()
            ax2 = self.figure_corte.add_subplot(111)
            
            b_line = np.linspace(10, 22, 200)
            p_line = []
            w_line = []
            
            for b in b_line:
                p, cl, w = self.calculate_physics(V_design, b, rho, k_wing, w_fixed, e_oswald, cd_profile, cd_parasitic, eta_total)
                p_line.append(p)
                w_line.append(w/9.81)
                
            color_p = '#004488'
            ax2.set_xlabel('Envergadura Alar [m]', fontsize=12)
            ax2.set_ylabel(f'Potencia a {V_design} m/s [W]', color=color_p, fontweight='bold', fontsize=12)
            ax2.plot(b_line, p_line, color=color_p, linewidth=3, label='Potencia Eléctrica')
            ax2.tick_params(axis='y', labelcolor=color_p)
            ax2.grid(True, linestyle='-', alpha=0.2)
            
            ax3 = ax2.twinx()
            color_w = '#882200'
            ax3.set_ylabel('Peso Total Resultante [kg]', color=color_w, fontweight='bold', fontsize=12)
            ax3.plot(b_line, w_line, color=color_w, linewidth=3, linestyle='--', label='Peso Total Estimado')
            ax3.tick_params(axis='y', labelcolor=color_w)
            
            idx_min = np.argmin(p_line)
            b_opt = b_line[idx_min]
            p_min = p_line[idx_min]
            w_opt = w_line[idx_min]
            
            ax2.plot(b_opt, p_min, marker='o', markersize=12, color='#FFD700', markeredgecolor='k', label='Óptimo Aerodinámico', zorder=10)
            ax2.axvline(x=b_opt, color='gray', linestyle=':', linewidth=2)
            
            label_opt = (f"ÓPTIMO A {V_design} m/s\nEnvergadura: {b_opt:.2f} m\nPotencia: {int(p_min)} W\nPeso: {w_opt:.1f} kg")
            ax2.annotate(label_opt, xy=(b_opt, p_min), xytext=(b_opt, p_min-30),
                         arrowprops=dict(facecolor='#FFD700', shrink=0.05),
                         bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black"), ha='center')
                         
            p_act, _, w_act = self.calculate_physics(V_design, 15.5, rho, k_wing, w_fixed, e_oswald, cd_profile, cd_parasitic, eta_total)
            ax2.plot(15.5, p_act, marker='s', color='#2C3E50', markersize=10, label='Diseño Actual (15.5m)', zorder=11)
            
            diff_watts = p_act - p_min
            ax2.annotate(f"Diferencia: +{int(diff_watts)} W\nvs Óptimo", xy=(15.5, p_act), xytext=(17, p_act+50),
                         arrowprops=dict(arrowstyle='->'), bbox=dict(boxstyle="round", fc="#eee"))
                         
            ax2.set_title(f'Compromiso Estructural a Velocidad de Diseño ({V_design} m/s)', fontsize=14, fontweight='bold')
            lines, labels = ax2.get_legend_handles_labels()
            lines2, labels2 = ax3.get_legend_handles_labels()
            ax2.legend(lines + lines2, labels + labels2, loc='upper center')
            
            self.figure_corte.tight_layout()
            self.canvas_corte.draw()
            
            # Interacción
            mplcursors.cursor(hover=True)
            
            # --- Exportar CSV ---
            import os
            export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data_processed")
            os.makedirs(export_dir, exist_ok=True)
            export_path = os.path.join(export_dir, "sizing_tradeoff.csv")
            
            df_export = pd.DataFrame({
                'Envergadura_m': b_line,
                'Potencia_W': p_line,
                'Peso_Total_kg': w_line
            })
            df_export.to_csv(export_path, index=False)
            
            self.status_label.setText(f"Mapa de Optimización generado. Óptimo: {b_opt:.2f}m. CSV Exportado.")
            self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            self.status_label.setText(f"Error generando Sizing: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.figure_mapa.tight_layout()
        self.canvas_mapa.draw_idle()
        self.figure_corte.tight_layout()
        self.canvas_corte.draw_idle()
