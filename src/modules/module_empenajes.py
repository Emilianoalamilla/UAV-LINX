# module_empenajes.py
import math
import numpy as np
import pandas as pd
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
from core.globals import UAVConstants

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
import mplcursors

class ControlSurface:
    def __init__(self, chord_ratio, span_ratio, max_deflection_deg):
        self.chord_ratio = chord_ratio  
        self.span_ratio = span_ratio    
        self.max_deflection = math.radians(max_deflection_deg)
        self.span = 0.0
        self.chord = 0.0
        self.area = 0.0

class Empennage:
    def __init__(self, area, span, distance_to_cg):
        self.area = area
        self.span = span
        self.distance_to_cg = distance_to_cg
        self.chord = self.area / self.span if self.span > 0 else 0

class VerticalTail(Empennage):
    def __init__(self, area, span, distance_to_cg, rudder):
        super().__init__(area, span, distance_to_cg)
        self.rudder = rudder
        
    def calculate_rudder_geometry(self):
        self.rudder.span = self.span * self.rudder.span_ratio
        self.rudder.chord = self.chord * self.rudder.chord_ratio
        self.rudder.area = self.rudder.span * self.rudder.chord
        return self.rudder

class HorizontalTail(Empennage):
    def __init__(self, area, span, distance_to_cg, elevator):
        super().__init__(area, span, distance_to_cg)
        self.elevator = elevator
        
    def calculate_elevator_geometry(self):
        self.elevator.span = self.span * self.elevator.span_ratio
        self.elevator.chord = self.chord * self.elevator.chord_ratio
        self.elevator.area = self.elevator.span * self.elevator.chord
        return self.elevator

class Aircraft:
    def __init__(self, mass, wing_area, wing_span, v_stall_ms, density_sl):
        self.mass = mass
        self.wing_area = wing_area
        self.wing_span = wing_span
        self.v_stall = v_stall_ms
        self.density = density_sl
        
        self.vertical_tail = None
        self.horizontal_tail = None

    def add_vertical_empennage(self, v_tail):
        self.vertical_tail = v_tail
        self.vertical_tail.calculate_rudder_geometry()

    def add_horizontal_empennage(self, h_tail):
        self.horizontal_tail = h_tail
        self.horizontal_tail.calculate_elevator_geometry()

    def calculate_min_controllable_speed(self, thrust_per_engine, engine_arms, cn_delta_r):
        asymmetric_moment = sum([thrust_per_engine * arm for arm in engine_arms])
        max_deflection = self.vertical_tail.rudder.max_deflection
        
        denominator = -0.5 * self.density * self.wing_area * self.wing_span * cn_delta_r * max_deflection
        if denominator <= 0:
            return float('inf')
        v_mc = math.sqrt(asymmetric_moment / denominator)
        return v_mc


class EmpenajesWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.setup_ui()
        self.procesar_empenajes()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Info Panel
        self.status_label = QLabel("Calculando Dimensionamiento de Empenajes...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        self.main_layout.addWidget(self.status_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Parámetro", "Valor", "Unidad"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setMaximumHeight(250)
        self.main_layout.addWidget(self.table)
        
        # Gráfica
        self.figure = Figure(figsize=(10, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.canvas)
        
    def procesar_empenajes(self):
        atm_df = self.data_loader.get_atmosfera_data()
        aero_df = self.data_loader.get_aerodinamica_data()
        
        try:
            # 1. Obtener densidad al nivel del mar
            rho_sl = 1.225
            if atm_df is not None:
                cols_atm = atm_df.columns.tolist()
                alt_col = next((c for c in cols_atm if 'altitud' in c.lower() or 'h' in c.lower() or '(m)' in c.lower()), cols_atm[0])
                rho_col = next((c for c in cols_atm if 'density' in c.lower() or 'densidad' in c.lower() or 'ρ' in c.lower()), None)
                idx_0 = (atm_df[alt_col] - 0).abs().idxmin()
                rho_sl = atm_df.loc[idx_0, rho_col]
                
            # 2. Obtener CL max para calcular V_stall dinámicamente
            cl_max = 1.5 # Fallback
            if aero_df is not None:
                cols_aero = aero_df.columns.tolist()
                cl_col = next((c for c in cols_aero if 'cl' in c.lower() or 'sust' in c.lower() and 'coef' in c.lower()), cols_aero[1])
                cl_max = aero_df[cl_col].max()
                
            mass = UAVConstants.WEIGHT_N / 9.81
            S_wing = UAVConstants.SURFACE_AREA
            b_wing = UAVConstants.WINGSPAN_M if hasattr(UAVConstants, 'WINGSPAN_M') else 15.5
            
            # Cálculo de V_stall
            v_stall_ms = math.sqrt((2 * UAVConstants.WEIGHT_N) / (rho_sl * S_wing * cl_max))
            
            # 3. Definir Aeronave HALE UAV
            uav = Aircraft(mass=mass, wing_area=S_wing, wing_span=b_wing, v_stall_ms=v_stall_ms, density_sl=rho_sl)
            
            # 4. Configurar Empenaje Vertical adaptado a nuestro HALE
            # HTail: Area ~ 10-15% del ala = 1.5m2, Span ~ 3m. Cola en V invertida o T-tail.
            rudder = ControlSurface(chord_ratio=0.3, span_ratio=1.0, max_deflection_deg=30)
            v_tail = VerticalTail(area=1.0, span=1.5, distance_to_cg=6.0, rudder=rudder)
            uav.add_vertical_empennage(v_tail)
            
            # 5. Configurar Empenaje Horizontal
            elevator = ControlSurface(chord_ratio=0.25, span_ratio=0.9, max_deflection_deg=25)
            h_tail = HorizontalTail(area=2.0, span=3.5, distance_to_cg=6.2, elevator=elevator)
            uav.add_horizontal_empennage(h_tail)
            
            # 6. Cálculo de V_MC (Falla de motor asimétrica)
            # Para el HALE, asumimos 2 motores eléctricos en las alas
            engine_arms = [4.0] # Un motor a 4m falla, genera momento
            thrust_per_engine = 60.0 # N de empuje máximo por motor a nivel del mar
            cn_delta_r = -0.136 
            
            v_mc = uav.calculate_min_controllable_speed(thrust_per_engine, engine_arms, cn_delta_r)
            ratio_vmc_vs = v_mc / v_stall_ms
            
            # 7. Llenar Tabla de Resultados
            results = [
                ("Masa Total", f"{uav.mass:.2f}", "kg"),
                ("Velocidad de Pérdida (V_stall) SL", f"{uav.v_stall:.2f}", "m/s"),
                ("Empenaje Vertical - Área", f"{v_tail.area:.2f}", "m²"),
                ("Timón (Rudder) - Cuerda", f"{v_tail.rudder.chord:.2f}", "m"),
                ("Timón (Rudder) - Área", f"{v_tail.rudder.area:.2f}", "m²"),
                ("Empenaje Horizontal - Área", f"{h_tail.area:.2f}", "m²"),
                ("Elevador - Cuerda", f"{h_tail.elevator.chord:.2f}", "m"),
                ("Elevador - Área", f"{h_tail.elevator.area:.2f}", "m²"),
                ("Velocidad Mínima Control (V_MC)", f"{v_mc:.2f}", "m/s"),
                ("Relación V_MC / V_stall", f"{ratio_vmc_vs:.2f}", "adimensional")
            ]
            
            self.table.setRowCount(len(results))
            for i, (param, val, unit) in enumerate(results):
                self.table.setItem(i, 0, QTableWidgetItem(param))
                self.table.setItem(i, 1, QTableWidgetItem(val))
                self.table.setItem(i, 2, QTableWidgetItem(unit))
                
            # 8. Graficar Geometría del Empenaje (Vista Planta)
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Estabilizador Horizontal
            ht_span = h_tail.span
            ht_chord = h_tail.chord
            y_ht = [-ht_span/2, ht_span/2, ht_span/2, -ht_span/2]
            x_ht = [0, 0, ht_chord, ht_chord]
            ht_poly = Polygon(xy=list(zip(y_ht, x_ht)), closed=True, facecolor='#e74c3c', edgecolor='#c0392b', alpha=0.5, label='Estabilizador Horiz.')
            ax.add_patch(ht_poly)
            
            # Elevador
            el_span = h_tail.elevator.span
            el_chord = h_tail.elevator.chord
            y_el = [-el_span/2, el_span/2, el_span/2, -el_span/2]
            x_el = [ht_chord - el_chord, ht_chord - el_chord, ht_chord, ht_chord]
            el_poly = Polygon(xy=list(zip(y_el, x_el)), closed=True, facecolor='#c0392b', edgecolor='black', alpha=0.9, hatch='//', label='Elevador')
            ax.add_patch(el_poly)
            
            # Estabilizador Vertical (Proyectado/Abatido 90 grados para vista)
            vt_span = v_tail.span
            vt_chord = v_tail.chord
            # Dibujarlo hacia arriba (Y positivo) para simular su forma
            y_vt = [0, vt_span, vt_span, 0]
            x_vt = [0, 0, vt_chord, vt_chord]
            vt_poly = Polygon(xy=list(zip(y_vt, x_vt)), closed=True, facecolor='#f1c40f', edgecolor='#f39c12', alpha=0.5, label='Estabilizador Vert. (Abatido)')
            ax.add_patch(vt_poly)
            
            # Timón
            ru_span = v_tail.rudder.span
            ru_chord = v_tail.rudder.chord
            y_ru = [0, ru_span, ru_span, 0]
            x_ru = [vt_chord - ru_chord, vt_chord - ru_chord, vt_chord, vt_chord]
            ru_poly = Polygon(xy=list(zip(y_ru, x_ru)), closed=True, facecolor='#f39c12', edgecolor='black', alpha=0.9, hatch='\\\\', label='Timón (Rudder)')
            ax.add_patch(ru_poly)
            
            ax.set_xlim(-ht_span/2 - 0.5, ht_span/2 + 0.5)
            ax.set_ylim(-0.5, max(ht_chord, vt_chord) + 0.5)
            ax.set_aspect('equal')
            ax.set_title(f'Configuración Geométrica del Grupo de Empenaje', fontsize=14, fontweight='bold')
            ax.set_xlabel('Envergadura (Y) [m]', fontsize=12)
            ax.set_ylabel('Cuerda (X) [m]', fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.legend()
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            # Interacción
            mplcursors.cursor(hover=True)
            
            self.status_label.setText(f"Cálculos Completados Exitosamente: V_MC = {v_mc:.2f} m/s")
            self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            self.status_label.setText(f"Error generando Empenajes: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.figure.tight_layout()
        self.canvas.draw_idle()
