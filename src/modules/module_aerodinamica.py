# module_aerodinamica.py
import pandas as pd
import numpy as np
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget)
from PySide6.QtCore import Qt

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import mplcursors

class AerodinamicaWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.setup_ui()
        self.procesar_datos()  # Cálculo automático al inicializar
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Panel Superior: Información y Resultados de Cálculos
        self.info_layout = QHBoxLayout()
        self.label_beta_max = QLabel("Beta Máximo (β_max): Calculando...")
        self.label_beta_max.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50;")
        
        self.info_layout.addWidget(self.label_beta_max)
        self.main_layout.addLayout(self.info_layout)
        
        # Tab Widget
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Tab 1: Coeficientes CL / CD
        self.tab_coef = QWidget()
        self.layout_coef = QVBoxLayout(self.tab_coef)
        self.figure_coef = Figure(figsize=(10, 6), dpi=100)
        self.canvas_coef = FigureCanvas(self.figure_coef)
        self.toolbar_coef = NavigationToolbar(self.canvas_coef, self)
        self.layout_coef.addWidget(self.toolbar_coef)
        self.layout_coef.addWidget(self.canvas_coef)
        self.tabs.addTab(self.tab_coef, "Curvas Lift / Drag")
        
        # Tab 2: Polares y Fineza
        self.tab_polar = QWidget()
        self.layout_polar = QVBoxLayout(self.tab_polar)
        self.figure_polar = Figure(figsize=(10, 6), dpi=100)
        self.canvas_polar = FigureCanvas(self.figure_polar)
        self.toolbar_polar = NavigationToolbar(self.canvas_polar, self)
        self.layout_polar.addWidget(self.toolbar_polar)
        self.layout_polar.addWidget(self.canvas_polar)
        self.tabs.addTab(self.tab_polar, "Polares y Fineza (Beta)")
        
    def procesar_datos(self):
        df = self.data_loader.get_aerodinamica_data()
        
        if df is None:
            self.label_beta_max.setText("Error: No se ha cargado el archivo CSV/XLS de aerodinámica.")
            self.label_beta_max.setStyleSheet("color: red;")
            return
            
        try:
            # Identificar las columnas reales del dataframe ya que pueden variar ligeramente por espacios
            cols = df.columns.tolist()
            
            # Buscamos heurísticamente las columnas clave
            alpha_col = next((c for c in cols if 'alpha' in c.lower() or 'ataq' in c.lower()), cols[0])
            cl_col = next((c for c in cols if 'cl' in c.lower() or 'sust' in c.lower() and 'coef' in c.lower()), cols[1])
            cd_col = next((c for c in cols if 'cd total' in c.lower() or 'cdt' in c.lower()), None)
            
            # Si no hay CD total pero sí CD ala, usamos CD ala.
            if cd_col is None:
                cd_col = next((c for c in cols if 'cd' in c.lower() or 'arrastre' in c.lower()), cols[2])
                
            # Cálculo de Beta (Fineza)
            df['Beta'] = df[cl_col] / df[cd_col]
            
            # Datos para graficar
            df_valid = df.copy()
            idx_beta_max = df_valid['Beta'].idxmax()
            beta_max = df_valid.loc[idx_beta_max, 'Beta']
            idx_stall = df_valid[cl_col].idxmax()
            cl_max = df_valid.loc[idx_stall, cl_col]
            
            self.label_beta_max.setText(f"β_max: {beta_max:.2f} (Alcanzado en α={df_valid.loc[idx_beta_max, alpha_col]}°, CL={df_valid.loc[idx_beta_max, cl_col]:.4f})")
            self.label_beta_max.setStyleSheet("font-size: 16px; font-weight: bold; color: #27AE60;")
            
            # --- Gráficas Tab 1: Lift / Drag ---
            self.figure_coef.clear()
            ax1 = self.figure_coef.add_subplot(121)
            ax2 = self.figure_coef.add_subplot(122)
            
            # 1. Alpha vs CL
            ax1.plot(df_valid[alpha_col], df_valid[cl_col], 'b-', linewidth=2)
            ax1.plot(df_valid.loc[idx_stall, alpha_col], df_valid.loc[idx_stall, cl_col], 'ro', label=f'Stall (CL={cl_max:.2f})')
            ax1.set_title('Coeficiente de Sustentación ($C_L$)', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Ángulo de Ataque $\\alpha$ [°]', fontsize=12)
            ax1.set_ylabel('$C_L$', fontsize=12)
            ax1.grid(True, linestyle='--', alpha=0.7)
            ax1.legend()
            
            # 2. Alpha vs CD
            ax2.plot(df_valid[alpha_col], df_valid[cd_col], 'r-', linewidth=2)
            ax2.set_title('Coeficiente de Arrastre ($C_D$)', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Ángulo de Ataque $\\alpha$ [°]', fontsize=12)
            ax2.set_ylabel('$C_D$', fontsize=12)
            ax2.grid(True, linestyle='--', alpha=0.7)
            
            self.figure_coef.tight_layout()
            self.canvas_coef.draw()
            
            # --- Gráficas Tab 2: Polares y Fineza ---
            self.figure_polar.clear()
            ax3 = self.figure_polar.add_subplot(121)
            ax4 = self.figure_polar.add_subplot(122)
            
            # 3. CD vs CL (Polar Aerodinámica)
            ax3.plot(df_valid[cd_col], df_valid[cl_col], 'g-', linewidth=2)
            ax3.plot(df_valid.loc[idx_beta_max, cd_col], df_valid.loc[idx_beta_max, cl_col], 'k*', markersize=10, label='Punto de Máxima Fineza')
            ax3.set_title('Polar Aerodinámica ($C_L$ vs $C_D$)', fontsize=14, fontweight='bold')
            ax3.set_xlabel('$C_D$', fontsize=12)
            ax3.set_ylabel('$C_L$', fontsize=12)
            ax3.grid(True, linestyle='--', alpha=0.7)
            ax3.legend()
            
            # 4. Alpha vs Beta (Fineza)
            ax4.plot(df_valid[alpha_col], df_valid['Beta'], 'm-', linewidth=2)
            ax4.plot(df_valid.loc[idx_beta_max, alpha_col], beta_max, 'k*', markersize=10, label=f'$\\beta_{{max}}$={beta_max:.2f}')
            ax4.set_title('Eficiencia Aerodinámica ($\\beta = C_L/C_D$)', fontsize=14, fontweight='bold')
            ax4.set_xlabel('Ángulo de Ataque $\\alpha$ [°]', fontsize=12)
            ax4.set_ylabel('Fineza $\\beta$', fontsize=12)
            ax4.grid(True, linestyle='--', alpha=0.7)
            ax4.legend()
            
            self.figure_polar.tight_layout()
            self.canvas_polar.draw()
            
            # Interacción
            mplcursors.cursor(hover=True)
            
        except Exception as e:
            self.label_beta_max.setText(f"Error al procesar los cálculos aerodinámicos: Falta información en el CSV ({str(e)})")
            self.label_beta_max.setStyleSheet("color: red;")
