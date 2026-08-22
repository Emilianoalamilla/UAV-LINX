# module_potencia.py
import numpy as np
import pandas as pd
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QTabWidget
from PySide6.QtCore import Qt
from core.globals import UAVConstants

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import mplcursors

class PotenciaWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.setup_ui()
        self.procesar_datos()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Info Panel
        self.status_label = QLabel("Calculando Potencias...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        self.main_layout.addWidget(self.status_label)
        
        # Tab Widget para organizar gráficas
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Tab 1: Altitud
        self.tab_altitud = QWidget()
        self.layout_altitud = QVBoxLayout(self.tab_altitud)
        self.figure_altitud = Figure(figsize=(10, 6), dpi=100)
        self.canvas_altitud = FigureCanvas(self.figure_altitud)
        self.toolbar_altitud = NavigationToolbar(self.canvas_altitud, self)
        self.layout_altitud.addWidget(self.toolbar_altitud)
        self.layout_altitud.addWidget(self.canvas_altitud)
        self.tabs.addTab(self.tab_altitud, "Potencia vs Altitud")
        
        # Tab 2: Envolvente de Velocidad
        self.tab_envolvente = QWidget()
        self.layout_envolvente = QVBoxLayout(self.tab_envolvente)
        self.figure_envolvente = Figure(figsize=(10, 6), dpi=100)
        self.canvas_envolvente = FigureCanvas(self.figure_envolvente)
        self.toolbar_envolvente = NavigationToolbar(self.canvas_envolvente, self)
        self.layout_envolvente.addWidget(self.toolbar_envolvente)
        self.layout_envolvente.addWidget(self.canvas_envolvente)
        self.tabs.addTab(self.tab_envolvente, "Potencia vs Velocidad")
        
    def procesar_datos(self):
        atm_df = self.data_loader.get_atmosfera_data()
        aero_df = self.data_loader.get_aerodinamica_data()
        
        if atm_df is None or aero_df is None:
            self.status_label.setText("Error: Faltan datos de Atmósfera o Aerodinámica.")
            self.status_label.setStyleSheet("color: red;")
            return
            
        try:
            # Columnas Atmósfera
            cols_atm = atm_df.columns.tolist()
            alt_col = next((c for c in cols_atm if 'altitud' in c.lower() or '- h -' in c.lower() or '(m)' in c.lower() or 'altitude' in c.lower()), cols_atm[0])
            rho_col = next((c for c in cols_atm if 'density' in c.lower() or 'densidad' in c.lower() or '- ρ -' in c.lower() and 'utm' not in c.lower()), None)
            
            # Columnas Aerodinámica
            cols_aero = aero_df.columns.tolist()
            alpha_col = next((c for c in cols_aero if 'alpha' in c.lower() or 'ataq' in c.lower()), cols_aero[0])
            cl_col = next((c for c in cols_aero if 'cl' in c.lower() or 'sust' in c.lower() and 'coef' in c.lower()), cols_aero[1])
            cd_col = next((c for c in cols_aero if 'cd total' in c.lower() or 'cdt' in c.lower()), None)
            if cd_col is None:
                cd_col = next((c for c in cols_aero if 'cd' in c.lower() or 'arrastre' in c.lower()), cols_aero[2])
                
            beta_col = next((c for c in cols_aero if 'fineza total' in c.lower() or 'beta t' in c.lower()), None)
            
            # Si no hay beta, lo calculamos
            if beta_col is None or beta_col not in aero_df.columns:
                beta = aero_df[cl_col] / aero_df[cd_col]
            else:
                beta = aero_df[beta_col]
                
            valid_idx = (aero_df[cl_col] > 0) & (beta > 0)
            cl_valid = aero_df.loc[valid_idx, cl_col]
            beta_valid = beta.loc[valid_idx]
            
            W = UAVConstants.WEIGHT_N
            S = UAVConstants.SURFACE_AREA
            
            # Eficiencias
            ef_wiring = 0.9
            ef_helice = 0.8
            ef_motor = 0.92
            ef_total = ef_wiring * ef_helice * ef_motor
            
            # --- ANÁLISIS AERODINÁMICO DE POTENCIA ---
            # Para vuelo nivelado, L = W, T = D. 
            # Potencia = T * V = D * V = W * (C_D / C_L) * V
            # V = sqrt(2W / (rho * S * C_L))
            # PR = sqrt(2W^3 / (rho * S)) * (C_D / C_L^1.5)
            # Por lo tanto:
            # 1. Potencia Mínima (Máxima Autonomía/Endurance) ocurre en max(C_L^1.5 / C_D)
            # 2. Potencia para Máximo Alcance (Max Range) ocurre en max(C_L / C_D) que es la Beta Máxima
            
            cl_15_cd = (cl_valid**1.5) / aero_df.loc[valid_idx, cd_col]
            
            idx_endurance = cl_15_cd.idxmax()
            idx_range = beta_valid.idxmax()
            
            # Valores aerodinámicos óptimos
            cl_end = cl_valid.loc[idx_endurance]
            beta_end = beta_valid.loc[idx_endurance]
            
            cl_rng = cl_valid.loc[idx_range]
            beta_rng = beta_valid.loc[idx_range]
            
            limit_alt = UAVConstants.MAX_ALTITUDE_M + 5000
            df_filtered = atm_df[atm_df[alt_col] <= limit_alt].copy()
            
            resultados = []
            
            for index, row in df_filtered.iterrows():
                alt = row[alt_col]
                rho = row[rho_col]
                if rho <= 0: continue
                
                # Velocidades óptimas para esta altitud
                v_endurance = np.sqrt((2 * W) / (rho * S * cl_end))
                v_range = np.sqrt((2 * W) / (rho * S * cl_rng))
                
                # Tracción requerida (T = W / beta)
                t_endurance = W / beta_end
                t_range = W / beta_rng
                
                # Potencia Requerida Real (PR = T * V / eficiencias)
                pr_endurance = (t_endurance * v_endurance) / ef_total
                pr_range = (t_range * v_range) / ef_total
                
                resultados.append({
                    'alt': alt,
                    'pr_endurance': pr_endurance,
                    'pr_range': pr_range,
                    'v_endurance': v_endurance,
                    'v_range': v_range
                })
                
            res_df = pd.DataFrame(resultados)
            
            # --- Gráfica 1: PR vs Altitud ---
            self.figure_altitud.clear()
            ax1 = self.figure_altitud.add_subplot(111)
            
            ax1.plot(res_df['pr_endurance'], res_df['alt'], label='PR (Máxima Autonomía)', color='green', linewidth=2.5)
            ax1.plot(res_df['pr_range'], res_df['alt'], label='PR (Máximo Alcance)', color='blue', linestyle='--', linewidth=2)
            ax1.axhline(y=UAVConstants.MAX_ALTITUDE_M, color='black', linestyle=':', label='Techo (25km)', linewidth=1.5)
            ax1.set_title('Potencia Requerida Real vs Altitud', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Potencia Eléctrica [W]', fontsize=12)
            ax1.set_ylabel('Altitud [m]', fontsize=12)
            ax1.legend(loc='lower right')
            ax1.grid(True, linestyle='--', alpha=0.7)
            
            self.figure_altitud.tight_layout()
            self.canvas_altitud.draw()
            
            # --- Gráfica 2: PR vs Velocidad ---
            self.figure_envolvente.clear()
            ax2 = self.figure_envolvente.add_subplot(111)
            
            target_alts = [0, 10000, 20000, UAVConstants.MAX_ALTITUDE_M]
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
            
            for i, alt_req in enumerate(target_alts):
                idx_closest = (atm_df[alt_col] - alt_req).abs().idxmin()
                rho_closest = atm_df.loc[idx_closest, rho_col]
                alt_closest = atm_df.loc[idx_closest, alt_col]
                
                V_alpha = np.sqrt((2 * W) / (rho_closest * S * cl_valid))
                Tr_array = W / beta_valid
                PR_real = (Tr_array * V_alpha) / ef_total
                
                mask = V_alpha < 100
                ax2.plot(V_alpha[mask], PR_real[mask], label=f'Alt: {alt_closest} m', color=colors[i], linewidth=2)
                
            ax2.set_title('Envolvente: Potencia Real vs Velocidad', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Velocidad [m/s]', fontsize=12)
            ax2.set_ylabel('Potencia Eléctrica [W]', fontsize=12)
            ax2.legend()
            ax2.grid(True, linestyle='--', alpha=0.7)
            
            self.figure_envolvente.tight_layout()
            self.canvas_envolvente.draw()
            
            # Interacción
            mplcursors.cursor(hover=True)
            
            # --- Exportar CSV ---
            import os
            export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data_processed")
            os.makedirs(export_dir, exist_ok=True)
            export_path = os.path.join(export_dir, "perfil_potencia.csv")
            res_df.to_csv(export_path, index=False)
            
            # Output label
            pr_25k = res_df[res_df['alt'] >= 25000]['pr_endurance'].iloc[0]
            v_25k = res_df[res_df['alt'] >= 25000]['v_endurance'].iloc[0]
            txt_res = f"Aerodinámica Óptima | Techo (25km): PR={pr_25k:.1f} W a {v_25k:.1f} m/s. CSV Exportado."
            self.status_label.setText(txt_res)
            self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            self.status_label.setText(f"Error en los cálculos: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.figure_altitud.tight_layout()
        self.canvas_altitud.draw_idle()
        self.figure_envolvente.tight_layout()
        self.canvas_envolvente.draw_idle()
