# module_velocidades.py
import numpy as np
import pandas as pd
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter)
from PySide6.QtCore import Qt
from core.globals import UAVConstants

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import mplcursors

class VelocidadesWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.setup_ui()
        self.procesar_velocidades() # Cálculo automático al inicializar
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Panel de Control
        self.ctrl_layout = QHBoxLayout()
        self.status_label = QLabel("Calculando...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        self.ctrl_layout.addWidget(self.status_label)
        self.main_layout.addLayout(self.ctrl_layout)
        
        # Canvas interactivo
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Envolver en un widget para el splitter
        canvas_widget = QWidget()
        canvas_layout = QVBoxLayout(canvas_widget)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.addWidget(self.toolbar)
        canvas_layout.addWidget(self.canvas)
        self.main_layout.addWidget(canvas_widget)
        
    def procesar_velocidades(self):
        atm_df = self.data_loader.get_atmosfera_data()
        aero_df = self.data_loader.get_aerodinamica_data()
        
        # Regla de Negocio: No deducir nada. Comprobar que existen los datos.
        if atm_df is None:
            self.status_label.setText("Error: Falta cargar el CSV/XLS de Atmósfera Estándar.")
            self.status_label.setStyleSheet("color: red;")
            return
            
        if aero_df is None:
            self.status_label.setText("Error: Falta cargar el CSV/XLS de Aerodinámica.")
            self.status_label.setStyleSheet("color: red;")
            return
            
        try:
            # Identificar columnas en Atmósfera (Altitud y Densidad)
            cols_atm = atm_df.columns.tolist()
            alt_col = next((c for c in cols_atm if 'altitud' in c.lower() or '- h -' in c.lower() or '(m)' in c.lower() or 'altitude' in c.lower()), cols_atm[0])
            rho_col = next((c for c in cols_atm if 'density' in c.lower() or 'densidad' in c.lower() or '- ρ -' in c.lower() and 'utm' not in c.lower()), None)
            
            if rho_col is None:
                raise ValueError("No se pudo encontrar la columna de Densidad (kg/m3) en el archivo de Atmósfera.")
                
            # Identificar columnas en Aerodinámica
            cols_aero = aero_df.columns.tolist()
            alpha_col = next((c for c in cols_aero if 'alpha' in c.lower() or 'ataq' in c.lower()), cols_aero[0])
            cl_col = next((c for c in cols_aero if 'cl' in c.lower() or 'sust' in c.lower() and 'coef' in c.lower()), cols_aero[1])
            cd_col = next((c for c in cols_aero if 'cd total' in c.lower() or 'cdt' in c.lower()), None)
            if cd_col is None:
                cd_col = next((c for c in cols_aero if 'cd' in c.lower() or 'arrastre' in c.lower()), cols_aero[2])
            
            # Buscar CL máximo (Stall), CL de fineza máxima (Crucero), CL mínimo (V max teórica sin contar empuje)
            cl_max = aero_df[cl_col].max()
            cl_min = aero_df[cl_col][aero_df[cl_col] > 0].min() # Asumimos CL positivo para vuelo recto y nivelado
            
            beta = aero_df[cl_col] / aero_df[cd_col]
            idx_cruise = beta.idxmax()
            cl_cruise = aero_df.loc[idx_cruise, cl_col]
            
            # Cálculos constantes
            W = UAVConstants.WEIGHT_N
            S = UAVConstants.SURFACE_AREA
            
            resultados = []
            
            # Por cada altitud, calcular V = sqrt( 2W / (rho * S * CL) )
            for index, row in atm_df.iterrows():
                alt = row[alt_col]
                rho = row[rho_col]
                
                # Evitar divisiones por cero si hay altitudes inválidas
                if rho <= 0:
                    continue
                    
                v_stall = np.sqrt((2 * W) / (rho * S * cl_max))
                v_cruise = np.sqrt((2 * W) / (rho * S * cl_cruise))
                v_max = np.sqrt((2 * W) / (rho * S * cl_min))
                
                resultados.append({
                    'alt': alt,
                    'v_stall': v_stall,
                    'v_cruise': v_cruise,
                    'v_max': v_max
                })
                
            res_df = pd.DataFrame(resultados)
            
            # --- Configuración de Gráficas ---
            self.figure.clear()
            ax1 = self.figure.add_subplot(121)
            ax2 = self.figure.add_subplot(122)
            
            # --- Gráfica 1: Perfil de Velocidades (Limitado a ~26km) ---
            ax1.plot(res_df['v_stall'], res_df['alt'], label='V Stall (Pérdida)', color='red')
            ax1.plot(res_df['v_cruise'], res_df['alt'], label='V Crucero (β máx)', color='green', linewidth=2)
            ax1.plot(res_df['v_max'], res_df['alt'], label='V Max (CL mín)', color='blue')
            
            ax1.axhline(y=UAVConstants.MAX_ALTITUDE_M, color='black', linestyle='--', label=f'Techo ({UAVConstants.MAX_ALTITUDE_M/1000} km)')
            
            ax1.set_title('Perfil de Velocidades (Log)')
            ax1.set_xlabel('Velocidad [m/s] (Escala Logarítmica)')
            ax1.set_ylabel('Altitud [m]')
            ax1.set_ylim(0, UAVConstants.MAX_ALTITUDE_M + 2000) # Límite Y relevante
            ax1.set_xscale('log') # Eje X en logaritmo como se solicitó
            ax1.legend()
            ax1.grid(True, which="both", linestyle='--', alpha=0.7)
            
            # --- Gráfica 2: Alpha vs Velocidad ---
            # Seleccionar alturas relevantes (e.g., Nivel del mar, 10km, 20km, 25km)
            target_alts = [0, 10000, 20000, UAVConstants.MAX_ALTITUDE_M]
            
            # Filtrar alphas donde CL > 0 para poder aplicar la raíz cuadrada real
            valid_aero = aero_df[aero_df[cl_col] > 0]
            
            for alt_req in target_alts:
                # Buscar la densidad más cercana a la altura solicitada
                idx_closest = (atm_df[alt_col] - alt_req).abs().idxmin()
                rho_closest = atm_df.loc[idx_closest, rho_col]
                alt_closest = atm_df.loc[idx_closest, alt_col]
                
                # Calcular vector de velocidades para cada alpha en esa altitud
                v_alpha = np.sqrt((2 * W) / (rho_closest * S * valid_aero[cl_col]))
                ax2.plot(valid_aero[alpha_col], v_alpha, label=f'Alt: {alt_closest} m')
                
            ax2.set_title('Alpha vs Velocidad (Por Altitud)')
            ax2.set_xlabel('Alpha [grados]')
            ax2.set_ylabel('Velocidad [m/s]')
            ax2.legend()
            ax2.grid(True, linestyle='--', alpha=0.7)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            # Interacción
            mplcursors.cursor(hover=True)
            
            # --- Exportar CSV ---
            import os
            export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data_processed")
            os.makedirs(export_dir, exist_ok=True)
            export_path = os.path.join(export_dir, "perfil_velocidades.csv")
            res_df.to_csv(export_path, index=False)
            
            self.status_label.setText(f"Cálculo Completo. Exportado a data_processed/perfil_velocidades.csv")
            self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            self.status_label.setText(f"Error en los cálculos: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.figure.tight_layout()
        self.canvas.draw_idle()
