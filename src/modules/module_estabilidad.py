import sys
import os
import numpy as np
import pandas as pd
from scipy import signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTabWidget, QTableWidget, QTableWidgetItem, 
                               QPushButton, QFileDialog, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import mplcursors

from core.globals import UAVConstants

try:
    from modules.latex_report_generator import generate_report
except ImportError:
    try:
        from .latex_report_generator import generate_report
    except ImportError:
        # Fallback si no existe el módulo
        def generate_report(results, filepath):
            pass


class EstabilidadWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.results = {}
        
        self.setup_ui()
        self.procesar_estabilidad()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Status Label
        self.status_label = QLabel("Inicializando módulo de estabilidad...")
        self.status_label.setStyleSheet("color: blue; font-weight: bold; padding: 5px;")
        self.main_layout.addWidget(self.status_label)
        
        # Tabs
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Tab 1: Estabilidad Longitudinal (Estática)
        self.tab_long = QWidget()
        self.layout_long = QVBoxLayout(self.tab_long)
        self.fig_long = Figure(figsize=(6, 4))
        self.canvas_long = FigureCanvas(self.fig_long)
        self.toolbar_long = NavigationToolbar(self.canvas_long, self.tab_long)
        self.layout_long.addWidget(self.toolbar_long)
        self.layout_long.addWidget(self.canvas_long, stretch=1)
        
        self.table_long = QTableWidget()
        self.table_long.setColumnCount(3)
        self.table_long.setHorizontalHeaderLabels(["Parámetro", "Valor", "Unidad"])
        self.table_long.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout_long.addWidget(self.table_long, stretch=1)
        self.tabs.addTab(self.tab_long, "Estabilidad Longitudinal (Estática)")
        
        # Tab 2: Estabilidad Direccional (Estática)
        self.tab_dir = QWidget()
        self.layout_dir = QVBoxLayout(self.tab_dir)
        self.fig_dir = Figure(figsize=(8, 4))
        self.canvas_dir = FigureCanvas(self.fig_dir)
        self.toolbar_dir = NavigationToolbar(self.canvas_dir, self.tab_dir)
        self.layout_dir.addWidget(self.toolbar_dir)
        self.layout_dir.addWidget(self.canvas_dir, stretch=1)
        
        self.table_dir = QTableWidget()
        self.table_dir.setColumnCount(3)
        self.table_dir.setHorizontalHeaderLabels(["Parámetro", "Valor", "Unidad"])
        self.table_dir.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout_dir.addWidget(self.table_dir, stretch=1)
        self.tabs.addTab(self.tab_dir, "Estabilidad Direccional (Estática)")
        
        # Tab 3: Estabilidad Dinámica
        self.tab_din = QWidget()
        self.layout_din = QVBoxLayout(self.tab_din)
        self.fig_din = Figure(figsize=(8, 8))
        self.canvas_din = FigureCanvas(self.fig_din)
        self.toolbar_din = NavigationToolbar(self.canvas_din, self.tab_din)
        self.layout_din.addWidget(self.toolbar_din)
        self.layout_din.addWidget(self.canvas_din, stretch=1)
        self.tabs.addTab(self.tab_din, "Estabilidad Dinámica")
        
        # Tab 4: Resumen y Exportar
        self.tab_res = QWidget()
        self.layout_res = QVBoxLayout(self.tab_res)
        
        self.table_res = QTableWidget()
        self.table_res.setColumnCount(4)
        self.table_res.setHorizontalHeaderLabels(["Criterio", "Valor", "Requisito", "Estado"])
        self.table_res.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout_res.addWidget(self.table_res)
        
        self.btn_layout = QHBoxLayout()
        self.btn_latex = QPushButton("Generar Reporte LaTeX")
        self.btn_latex.clicked.connect(self.exportar_latex)
        self.btn_csv = QPushButton("Exportar CSV")
        self.btn_csv.clicked.connect(self.exportar_csv)
        self.btn_layout.addWidget(self.btn_latex)
        self.btn_layout.addWidget(self.btn_csv)
        self.layout_res.addLayout(self.btn_layout)
        
        self.tabs.addTab(self.tab_res, "Resumen y Exportar")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            self.fig_long.tight_layout()
            self.canvas_long.draw_idle()
            self.fig_dir.tight_layout()
            self.canvas_dir.draw_idle()
            self.fig_din.tight_layout()
            self.canvas_din.draw_idle()
        except Exception:
            pass

    def procesar_estabilidad(self):
        try:
            # Obtener datos aerodinámicos
            df_aero = self.data_loader.get_aerodinamica_data()
            if df_aero is None or df_aero.empty:
                raise ValueError("No se encontraron datos aerodinámicos.")
            
            # Buscar columnas heurísticamente
            col_alpha = next((col for col in df_aero.columns if 'alpha' in col.lower() or 'alfa' in col.lower() or 'ang' in col.lower() or 'ángulo' in col.lower()), None)
            col_cl = next((col for col in df_aero.columns if 'cl' in col.lower() or 'lift' in col.lower() or 'sust' in col.lower()), None)
            col_cd = next((col for col in df_aero.columns if 'cd' in col.lower() or 'drag' in col.lower() or 'arrastre' in col.lower()), None)
            
            if not all([col_alpha, col_cl, col_cd]):
                raise ValueError("No se encontraron las columnas necesarias (alpha, CL, CD) en los datos.")
            
            alpha_deg = df_aero[col_alpha].values
            cl_vals = df_aero[col_cl].values
            cd_vals = df_aero[col_cd].values
            
            # --- 1. Estabilidad Longitudinal ---
            mask_lin = (alpha_deg >= -5) & (alpha_deg <= 10)
            if not np.any(mask_lin):
                mask_lin = (alpha_deg >= np.min(alpha_deg)) & (alpha_deg <= np.max(alpha_deg))
                
            p_cl = np.polyfit(alpha_deg[mask_lin], cl_vals[mask_lin], 1)
            CL_alpha_deg = p_cl[0]
            CL_alpha = CL_alpha_deg * (180.0 / np.pi)
            
            # Alpha 0L
            alpha_0L_deg = -p_cl[1] / p_cl[0] if p_cl[0] != 0 else 0
            alpha_0L = np.radians(alpha_0L_deg)
            
            V_H = (UAVConstants.S_HTAIL * UAVConstants.L_HTAIL) / (UAVConstants.SURFACE_AREA * UAVConstants.MAC)
            de_da = 2 * CL_alpha / (np.pi * UAVConstants.ASPECT_RATIO)
            
            AR_h = (UAVConstants.SPAN_HTAIL**2) / UAVConstants.S_HTAIL
            CL_alpha_h = 2 * np.pi * 0.9 * (AR_h / (AR_h + 2))
            
            x_cg = UAVConstants.CG_POSITION_MAC * UAVConstants.MAC
            x_ac = UAVConstants.AC_POSITION_MAC * UAVConstants.MAC
            
            Cm_alpha = CL_alpha * (x_cg - x_ac)/UAVConstants.MAC - UAVConstants.ETA_H * V_H * CL_alpha_h * (1 - de_da)
            x_NP_mac = UAVConstants.AC_POSITION_MAC + (UAVConstants.ETA_H * V_H * CL_alpha_h * (1 - de_da) / CL_alpha)
            x_NP = x_NP_mac * UAVConstants.MAC
            
            Static_Margin = x_NP_mac - UAVConstants.CG_POSITION_MAC
            Cm_0 = -Cm_alpha * alpha_0L
            Cm_de = -UAVConstants.ETA_H * V_H * CL_alpha_h * UAVConstants.TAU_ELEVATOR
            
            self.results.update({
                'CL_alpha (1/rad)': CL_alpha,
                'V_H': V_H,
                'de_da': de_da,
                'CL_alpha_h (1/rad)': CL_alpha_h,
                'Cm_alpha (1/rad)': Cm_alpha,
                'x_NP (m)': x_NP,
                'Static Margin (%)': Static_Margin * 100,
                'Cm_0': Cm_0,
                'Cm_de (1/rad)': Cm_de
            })
            
            # --- 2. Estabilidad Direccional ---
            V_V = (UAVConstants.S_VTAIL * UAVConstants.L_VTAIL) / (UAVConstants.SURFACE_AREA * UAVConstants.WINGSPAN)
            AR_v = (UAVConstants.SPAN_VTAIL**2) / UAVConstants.S_VTAIL
            CL_alpha_v = 2 * np.pi * 0.85 * (AR_v / (AR_v + 2))
            
            Cn_beta = UAVConstants.ETA_V * V_V * CL_alpha_v
            dihedral_rad = np.radians(UAVConstants.DIHEDRAL_DEG)
            Cl_beta = -(UAVConstants.CL_REF / 4) * dihedral_rad
            Cn_dr = -UAVConstants.ETA_V * V_V * CL_alpha_v * UAVConstants.TAU_RUDDER
            
            y1 = UAVConstants.AILERON_Y_INNER * UAVConstants.WINGSPAN / 2
            y2 = UAVConstants.AILERON_Y_OUTER * UAVConstants.WINGSPAN / 2
            integral_aileron = UAVConstants.MAC * (y2**2 - y1**2) / 2
            Cl_da = (2 * CL_alpha * UAVConstants.TAU_AILERON / (UAVConstants.SURFACE_AREA * UAVConstants.WINGSPAN)) * integral_aileron
            
            self.results.update({
                'V_V': V_V,
                'CL_alpha_v (1/rad)': CL_alpha_v,
                'Cn_beta (1/rad)': Cn_beta,
                'Cl_beta (1/rad)': Cl_beta,
                'Cn_dr (1/rad)': Cn_dr,
                'Cl_da (1/rad)': Cl_da
            })
            
            # --- 3. Estabilidad Dinámica ---
            m = UAVConstants.MASS_KG
            rho = UAVConstants.RHO_25KM
            S = UAVConstants.SURFACE_AREA
            u0 = UAVConstants.VELOCITY_REF
            b = UAVConstants.WINGSPAN
            c = UAVConstants.MAC
            g = 9.81
            
            Ixx = (1/12) * m * b**2
            Iyy = (1/12) * m * c**2
            Izz = Ixx + Iyy
            
            # CD_alpha aprox
            p_cd = np.polyfit(alpha_deg[mask_lin], cd_vals[mask_lin], 2)
            CD0 = np.polyval(p_cd, 0)
            CD_alpha = (np.polyval(p_cd, 1) - np.polyval(p_cd, -1)) / (2 * np.radians(1)) * (180.0/np.pi)
            
            Xu = -rho * S * u0 * (2 * CD0) / (2 * m)
            Xw = rho * S * u0 * (UAVConstants.CL_REF - 2 * CD_alpha) / (2 * m)
            Zu = -rho * S * u0 * (2 * UAVConstants.CL_REF) / (2 * m)
            Zw = -rho * S * u0 * (CL_alpha + CD0) / (2 * m)
            
            Cm_u = 0.0
            Mu = rho * S * u0 * c * (2 * Cm_u) / (2 * Iyy)
            Mw = rho * S * u0 * c * Cm_alpha / (2 * Iyy)
            
            Cm_q = -2 * UAVConstants.ETA_H * V_H * CL_alpha_h * UAVConstants.L_HTAIL / c
            Mq = rho * S * u0 * c**2 * Cm_q / (4 * Iyy)
            
            A_lon = np.array([
                [Xu, Xw, 0, -g],
                [Zu, Zw, u0, 0],
                [Mu, Mw, Mq, 0],
                [0, 0, 1, 0]
            ])
            eigs_lon = np.linalg.eigvals(A_lon)
            
            # Ordenar autovalores longitudinales
            idx_lon = np.argsort(np.abs(eigs_lon))[::-1]
            eigs_lon_sorted = eigs_lon[idx_lon]
            sp_mode = eigs_lon_sorted[0:2] # Short period (mayor magnitud)
            ph_mode = eigs_lon_sorted[2:4] # Phugoid
            
            # Dinámica lateral
            CY_beta = -UAVConstants.ETA_V * UAVConstants.S_VTAIL / S * CL_alpha_v
            Yv = -rho * S * u0 * CY_beta / (2 * m)
            Lv = rho * S * u0 * b * Cl_beta / (2 * Ixx)
            Cl_r = UAVConstants.CL_REF / 4
            Lr = rho * S * u0 * b**2 * Cl_r / (4 * Ixx)
            Cl_p = -CL_alpha / 12
            Lp = rho * S * u0 * b**2 * Cl_p / (4 * Ixx)
            Nv = rho * S * u0 * b * Cn_beta / (2 * Izz)
            Cn_r = -2 * UAVConstants.ETA_V * V_V * CL_alpha_v * UAVConstants.L_VTAIL / b
            Nr = rho * S * u0 * b**2 * Cn_r / (4 * Izz)
            Cn_p = -UAVConstants.CL_REF / 8
            Np = rho * S * u0 * b**2 * Cn_p / (4 * Izz)
            
            A_lat = np.array([
                [Yv, g/u0, 0, -1],
                [0, 0, 1, 0],
                [Lv, 0, Lp, Lr],
                [Nv, 0, Np, Nr]
            ])
            eigs_lat = np.linalg.eigvals(A_lat)
            
            # Identificar modos laterales
            dr_idx = np.where(np.abs(np.imag(eigs_lat)) > 1e-3)[0]
            if len(dr_idx) >= 2:
                dr_mode = eigs_lat[dr_idx[:2]]
                real_eigs = np.delete(eigs_lat, dr_idx[:2])
            else:
                dr_mode = np.array([np.nan, np.nan])
                real_eigs = eigs_lat
                
            real_eigs_sorted = np.sort(np.real(real_eigs))
            spiral_mode = real_eigs_sorted[-1] if len(real_eigs) > 0 else np.nan
            roll_mode = real_eigs_sorted[0] if len(real_eigs) > 1 else np.nan
            
            self.results['Eigs Longitudinal'] = eigs_lon
            self.results['Eigs Lateral'] = eigs_lat
            
            # --- Actualizar Tablas ---
            self.poblar_tabla_long()
            self.poblar_tabla_dir()
            
            # --- Actualizar Gráficos ---
            self.plot_longitudinal(alpha_deg, Cm_alpha, Cm_0)
            self.plot_direccional(Cn_beta, Cl_beta)
            self.plot_dinamica(A_lon, eigs_lon, eigs_lat, sp_mode, ph_mode, dr_mode, roll_mode, spiral_mode)
            
            # --- Actualizar Resumen ---
            self.poblar_resumen(Cm_alpha, Cn_beta, Cl_beta, Static_Margin, sp_mode, dr_mode, eigs_lon, eigs_lat)
            
            self.status_label.setText("Cálculos de estabilidad completados exitosamente.")
            self.status_label.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
            
        except Exception as e:
            self.status_label.setText(f"Error procesando estabilidad: {str(e)}")
            self.status_label.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
            print(f"Error: {e}")

    def poblar_tabla_long(self):
        self.table_long.setRowCount(0)
        keys = ['CL_alpha (1/rad)', 'V_H', 'de_da', 'CL_alpha_h (1/rad)', 'Cm_alpha (1/rad)', 
                'x_NP (m)', 'Static Margin (%)', 'Cm_0', 'Cm_de (1/rad)']
        for key in keys:
            if key in self.results:
                row = self.table_long.rowCount()
                self.table_long.insertRow(row)
                parts = key.split(' (')
                name = parts[0]
                unit = '(' + parts[1] if len(parts) > 1 else '-'
                
                self.table_long.setItem(row, 0, QTableWidgetItem(name))
                self.table_long.setItem(row, 1, QTableWidgetItem(f"{self.results[key]:.4f}"))
                self.table_long.setItem(row, 2, QTableWidgetItem(unit.replace('(', '').replace(')', '')))

    def poblar_tabla_dir(self):
        self.table_dir.setRowCount(0)
        keys = ['V_V', 'CL_alpha_v (1/rad)', 'Cn_beta (1/rad)', 'Cl_beta (1/rad)', 'Cn_dr (1/rad)', 'Cl_da (1/rad)']
        for key in keys:
            if key in self.results:
                row = self.table_dir.rowCount()
                self.table_dir.insertRow(row)
                parts = key.split(' (')
                name = parts[0]
                unit = '(' + parts[1] if len(parts) > 1 else '-'
                
                self.table_dir.setItem(row, 0, QTableWidgetItem(name))
                self.table_dir.setItem(row, 1, QTableWidgetItem(f"{self.results[key]:.4f}"))
                self.table_dir.setItem(row, 2, QTableWidgetItem(unit.replace('(', '').replace(')', '')))

    def poblar_resumen(self, Cm_alpha, Cn_beta, Cl_beta, SM, sp_mode, dr_mode, eigs_lon, eigs_lat):
        self.table_res.setRowCount(0)
        
        criterios = [
            ("Estabilidad Longitudinal Estática (Cm_alpha)", Cm_alpha, "< 0", Cm_alpha < 0),
            ("Estabilidad Direccional (Cn_beta)", Cn_beta, "> 0", Cn_beta > 0),
            ("Efecto Diédro (Cl_beta)", Cl_beta, "< 0", Cl_beta < 0),
            ("Margen Estático", SM * 100, "5% - 15%", 0.05 <= SM <= 0.15),
            ("Modos Longitudinales Estables", np.max(np.real(eigs_lon)), "Re(λ) < 0", np.max(np.real(eigs_lon)) < 0),
            ("Modos Laterales Estables", np.max(np.real(eigs_lat)), "Re(λ) < 0", np.max(np.real(eigs_lat)) < 0),
        ]
        
        # Amortiguamiento Short Period
        if len(sp_mode) > 0:
            zeta_sp = -np.real(sp_mode[0]) / np.abs(sp_mode[0])
            criterios.append(("Amortiguamiento Short Period", zeta_sp, "0.3 - 2.0", 0.3 <= zeta_sp <= 2.0))
            
        # Amortiguamiento Dutch Roll
        if not np.isnan(dr_mode[0]):
            zeta_dr = -np.real(dr_mode[0]) / np.abs(dr_mode[0])
            criterios.append(("Amortiguamiento Dutch Roll", zeta_dr, "> 0.05", zeta_dr > 0.05))
            
        for crit, val, req, status in criterios:
            row = self.table_res.rowCount()
            self.table_res.insertRow(row)
            
            self.table_res.setItem(row, 0, QTableWidgetItem(crit))
            self.table_res.setItem(row, 1, QTableWidgetItem(f"{val:.4f}"))
            self.table_res.setItem(row, 2, QTableWidgetItem(req))
            
            status_item = QTableWidgetItem("✓ Cumple" if status else "✗ No Cumple")
            color = QColor("lightgreen") if status else QColor("lightcoral")
            if crit == "Margen Estático" and not status:
                if SM > 0:
                    status_item.setText("⚠ Revisar (Demasiado Estable)")
                    color = QColor("lightyellow")
            status_item.setBackground(color)
            self.table_res.setItem(row, 3, status_item)

    def plot_longitudinal(self, alpha_deg, Cm_alpha, Cm_0):
        self.fig_long.clear()
        ax = self.fig_long.add_subplot(111)
        
        alphas = np.linspace(-10, 15, 100)
        alphas_rad = np.radians(alphas)
        Cm = Cm_0 + Cm_alpha * alphas_rad
        
        ax.plot(alphas, Cm, 'b-', linewidth=2, label='Cm vs α')
        ax.axhline(0, color='k', linestyle='--', linewidth=1)
        ax.axvline(0, color='k', linestyle='--', linewidth=1)
        
        # Trim point
        if Cm_alpha != 0:
            alpha_trim = -Cm_0 / Cm_alpha
            alpha_trim_deg = np.degrees(alpha_trim)
            if -10 <= alpha_trim_deg <= 15:
                ax.plot(alpha_trim_deg, 0, 'ro', markersize=8, label=f'Trim: {alpha_trim_deg:.1f}°')
                
        ax.set_xlabel('Ángulo de Ataque α (grados)')
        ax.set_ylabel('Coeficiente de Momento Cm')
        ax.set_title('Estabilidad Longitudinal Estática')
        ax.grid(True, linestyle=':', alpha=0.7)
        ax.legend()
        
        cursor = mplcursors.cursor(ax.lines, hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(f"α={sel.target[0]:.1f}°, Cm={sel.target[1]:.3f}"))
        
        self.fig_long.tight_layout()
        self.canvas_long.draw_idle()

    def plot_direccional(self, Cn_beta, Cl_beta):
        self.fig_dir.clear()
        
        betas = np.linspace(-15, 15, 100)
        betas_rad = np.radians(betas)
        
        Cn = Cn_beta * betas_rad
        Cl = Cl_beta * betas_rad
        
        ax1 = self.fig_dir.add_subplot(121)
        ax1.plot(betas, Cn, 'g-', linewidth=2, label='Cn vs β')
        ax1.axhline(0, color='k', linestyle='--', linewidth=1)
        ax1.axvline(0, color='k', linestyle='--', linewidth=1)
        ax1.set_xlabel('Ángulo de Resbalamiento β (grados)')
        ax1.set_ylabel('Cn (Momento de Guiñada)')
        ax1.set_title('Estabilidad Direccional (Veleta)')
        ax1.grid(True, linestyle=':', alpha=0.7)
        ax1.legend()
        
        ax2 = self.fig_dir.add_subplot(122)
        ax2.plot(betas, Cl, 'm-', linewidth=2, label='Cl vs β')
        ax2.axhline(0, color='k', linestyle='--', linewidth=1)
        ax2.axvline(0, color='k', linestyle='--', linewidth=1)
        ax2.set_xlabel('Ángulo de Resbalamiento β (grados)')
        ax2.set_ylabel('Cl (Momento de Alabeo)')
        ax2.set_title('Efecto Diédro')
        ax2.grid(True, linestyle=':', alpha=0.7)
        ax2.legend()
        
        mplcursors.cursor(ax1.lines, hover=True)
        mplcursors.cursor(ax2.lines, hover=True)
        
        self.fig_dir.tight_layout()
        self.canvas_dir.draw_idle()

    def plot_dinamica(self, A_lon, eigs_lon, eigs_lat, sp_mode, ph_mode, dr_mode, roll_mode, spiral_mode):
        self.fig_din.clear()
        
        # Subplot 1: Mapa de Polos Longitudinal
        ax1 = self.fig_din.add_subplot(221)
        ax1.scatter(np.real(sp_mode), np.imag(sp_mode), marker='x', color='r', s=100, label='Short Period')
        ax1.scatter(np.real(ph_mode), np.imag(ph_mode), marker='o', color='b', s=100, label='Phugoid')
        ax1.axvline(0, color='k', linestyle='-')
        ax1.axhline(0, color='k', linestyle='-')
        ax1.set_xlabel('Re')
        ax1.set_ylabel('Im')
        ax1.set_title('Modos Longitudinales')
        ax1.grid(True, linestyle=':')
        ax1.legend()
        
        # Subplot 2: Mapa de Polos Lateral
        ax2 = self.fig_din.add_subplot(222)
        if not np.isnan(dr_mode[0]):
            ax2.scatter(np.real(dr_mode), np.imag(dr_mode), marker='d', color='g', s=100, label='Dutch Roll')
        if not np.isnan(roll_mode):
            ax2.scatter(np.real(roll_mode), 0, marker='s', color='m', s=100, label='Roll')
        if not np.isnan(spiral_mode):
            ax2.scatter(np.real(spiral_mode), 0, marker='^', color='c', s=100, label='Spiral')
        ax2.axvline(0, color='k', linestyle='-')
        ax2.axhline(0, color='k', linestyle='-')
        ax2.set_xlabel('Re')
        ax2.set_ylabel('Im')
        ax2.set_title('Modos Laterales-Direccionales')
        ax2.grid(True, linestyle=':')
        ax2.legend()
        
        # Subplot 3: Respuesta al Escalón (Elevador)
        ax3 = self.fig_din.add_subplot(212)
        
        # Sistema de espacio de estados para respuesta al escalón: delta_e
        # Matriz B para elevador (simplificada)
        rho = UAVConstants.RHO_25KM
        u0 = UAVConstants.VELOCITY_REF
        S = UAVConstants.SURFACE_AREA
        c = UAVConstants.MAC
        m = UAVConstants.MASS_KG
        Iyy = (1/12) * m * c**2
        
        X_de = 0.0
        Z_de = -rho * S * u0**2 * 0.1 / (2 * m) # Aproximación
        M_de = rho * S * u0**2 * c * self.results.get('Cm_de (1/rad)', -1.0) / (2 * Iyy)
        
        B_lon = np.array([[X_de], [Z_de], [M_de], [0]])
        C_lon = np.eye(4)
        D_lon = np.zeros((4, 1))
        
        sys_lon = signal.StateSpace(A_lon, B_lon, C_lon, D_lon)
        t = np.linspace(0, 50, 1000)
        u_step = np.ones_like(t) * np.radians(-1) # 1 grado up-elevator
        
        try:
            t_out, y_out, _ = signal.lsim(sys_lon, U=u_step, T=t)
            
            ax3.plot(t_out, y_out[:, 0], label='Δu (m/s)')
            ax3.plot(t_out, y_out[:, 1], label='Δw (m/s)')
            ax3.plot(t_out, np.degrees(y_out[:, 2]), label='Δq (deg/s)')
            ax3.plot(t_out, np.degrees(y_out[:, 3]), label='Δθ (deg)')
            ax3.set_xlabel('Tiempo (s)')
            ax3.set_ylabel('Respuesta')
            ax3.set_title('Respuesta al Escalón: Elevador (-1°)')
            ax3.grid(True, linestyle=':')
            ax3.legend()
        except Exception as e:
            ax3.text(0.5, 0.5, f"Error en simulación: {e}", ha='center', va='center')
        
        mplcursors.cursor(ax1.collections, hover=True)
        mplcursors.cursor(ax2.collections, hover=True)
        
        self.fig_din.tight_layout()
        self.canvas_din.draw_idle()

    def exportar_latex(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar Reporte LaTeX", "", "LaTeX Files (*.tex)")
        if filename:
            try:
                generate_report(self.results, filename)
                QMessageBox.information(self, "Éxito", f"Reporte exportado exitosamente a:\n{filename}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Fallo al exportar reporte LaTeX:\n{str(e)}")

    def exportar_csv(self):
        try:
            os.makedirs("data_processed", exist_ok=True)
            filepath = os.path.join("data_processed", "estabilidad_derivativos.csv")
            
            df = pd.DataFrame(list(self.results.items()), columns=["Parámetro", "Valor"])
            df.to_csv(filepath, index=False)
            
            QMessageBox.information(self, "Éxito", f"Datos exportados exitosamente a:\n{filepath}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo al exportar CSV:\n{str(e)}")
