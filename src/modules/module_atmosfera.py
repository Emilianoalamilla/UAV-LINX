# module_atmosfera.py
import numpy as np
import pandas as pd
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from core.globals import UAVConstants

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import mplcursors

class AtmosferaWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.setup_ui()
        self.procesar_datos()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Label de estado
        self.status_label = QLabel("Calculando perfil atmosférico...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        self.main_layout.addWidget(self.status_label)
        
        # Gráfica interactiva
        self.figure = Figure(figsize=(15, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.canvas)
        
    def procesar_datos(self):
        atm_df = self.data_loader.get_atmosfera_data()
        
        if atm_df is None:
            self.status_label.setText("Error: Falta cargar el CSV/XLS de Atmósfera Estándar.")
            self.status_label.setStyleSheet("color: red;")
            return
            
        try:
            # Identificar columnas
            cols_atm = atm_df.columns.tolist()
            alt_col = next((c for c in cols_atm if 'altitud' in c.lower() or '- h -' in c.lower() or '(m)' in c.lower() or 'altitude' in c.lower()), cols_atm[0])
            temp_col = next((c for c in cols_atm if 'temp' in c.lower() or 't -' in c.lower()), cols_atm[1])
            rho_col = next((c for c in cols_atm if 'density' in c.lower() or 'densidad' in c.lower() or '- ρ -' in c.lower() and 'utm' not in c.lower()), None)
            mu_col = next((c for c in cols_atm if 'viscosidad' in c.lower() or 'viscosity' in c.lower() or 'μ' in c.lower()), None)
            
            # Limitar altitud hasta 35 km (o el techo + 10km)
            limit_alt = UAVConstants.MAX_ALTITUDE_M + 10000
            df_filtered = atm_df[atm_df[alt_col] <= limit_alt].copy()
            
            alt_km = df_filtered[alt_col] / 1000.0
            temp_c = df_filtered[temp_col]
            dens_kgm3 = df_filtered[rho_col]
            
            # --- Perfil de Viento Empírico (CDMX/Latitud 19°N interpolado) ---
            viento_base_alt_km = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35])
            viento_base_ms = np.array([3.0, 4.2, 5.5, 7.0, 8.5, 11.0, 14.0, 18.0, 22.0, 26.0, 30.0, 35.0, 20.0, 12.0, 8.0, 15.0])
            # Interpolar para las alturas del CSV
            viento_ms = np.interp(alt_km, viento_base_alt_km, viento_base_ms)
            
            # --- Cálculo de Reynolds ---
            # Re = (rho * V_vuelo * MAC) / mu
            # Para esto podemos asumir que el avión vuela a la V de diseño (39 m/s) o usar los datos
            v_vuelo = UAVConstants.VELOCITY_REF
            mac = UAVConstants.MAC
            if mu_col is not None:
                mu = df_filtered[mu_col]
                # Asegurar que mu no sea string debido a limpieza
                mu = pd.to_numeric(mu, errors='coerce').fillna(1.8e-5) # fallback fallback
                reynolds = (dens_kgm3 * v_vuelo * mac) / mu
                # Normalizar para graficar en e^5 o similar (el usuario lo tenía en escala pequeña, ej 1.09)
                reynolds = reynolds / 1e6 # En Millones
                rey_label = 'Reynolds [Millones]'
            else:
                # Si no hay mu, interpolamos la tabla manual del usuario
                rey_base_km = np.array([0, 15, 20, 25, 30, 35])
                rey_base_val = np.array([4.91, 2.46, 1.66, 1.09, 0.73, 0.54])
                reynolds = np.interp(alt_km, rey_base_km, rey_base_val)
                rey_label = 'Reynolds [Escala]'
            
            # --- Configuración de Gráficas ---
            self.figure.clear()
            axs = self.figure.subplots(1, 4, sharey=True)
            self.figure.subplots_adjust(wspace=0)
            
            colors = ['#1f77b4', '#2ca02c', '#d62728', '#ff7f0e']
            labels = ['Temperatura [°C]', 'Densidad [kg/m³]', 'Velocidad Viento [m/s]', rey_label]
            
            # Configuración general
            for i, ax in enumerate(axs):
                ax.grid(True, linestyle='--', alpha=0.6)
                ax.spines['top'].set_visible(False)
                if i > 0:
                    ax.spines['left'].set_color('gray')
                    ax.tick_params(axis='y', length=0)
            
            # Panel 1: Temperatura
            axs[0].plot(temp_c, alt_km, color=colors[0], linewidth=2)
            axs[0].set_xlabel(labels[0], fontweight='bold')
            axs[0].set_ylabel('Altitud [km]', fontsize=12, fontweight='bold')
            
            # Panel 2: Densidad
            axs[1].plot(dens_kgm3, alt_km, color=colors[1], linewidth=2)
            axs[1].set_xlabel(labels[1], fontweight='bold')
            # Poner escala log en densidad si se aplana mucho
            axs[1].set_xscale('log')
            
            # Panel 3: Velocidad del Viento
            axs[2].plot(viento_ms, alt_km, color=colors[2], linewidth=2)
            axs[2].set_xlabel(labels[2], fontweight='bold')
            
            # Panel 4: Reynolds
            axs[3].plot(reynolds, alt_km, color=colors[3], linewidth=2)
            axs[3].set_xlabel(labels[3], fontweight='bold')
            
            # Resaltar la Tropopausa (~11 a 16 km)
            for ax in axs:
                ax.axhspan(11, 16, color='yellow', alpha=0.15)
            axs[1].text(0.1, 13.5, 'TROPOPAUSA', color='orange', weight='bold', ha='center', transform=axs[1].get_yaxis_transform())
            
            self.figure.suptitle('Perfil Atmosférico (Datos Dinámicos + CDMX)', fontsize=16)
            self.figure.tight_layout()
            self.figure.subplots_adjust(top=0.92)
            self.canvas.draw()
            
            # Interacción
            mplcursors.cursor(hover=True)
            
            # --- Exportar CSV ---
            import os
            export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data_processed")
            os.makedirs(export_dir, exist_ok=True)
            export_path = os.path.join(export_dir, "perfil_atmosferico.csv")
            
            # Agregar viento y reynolds al df exportable
            df_export = df_filtered.copy()
            df_export['Viento_Empirico_ms'] = viento_ms
            df_export['Reynolds_Millones'] = reynolds
            df_export.to_csv(export_path, index=False)
            
            self.status_label.setText("Perfil Atmosférico generado. CSV Exportado.")
            self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            self.status_label.setText(f"Error generando perfil atmosférico: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
