# module_mision_perfil.py
import numpy as np
import matplotlib
matplotlib.use('QtAgg')
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from core.globals import UAVConstants

# PALETA DE COLORES
BG       = "#ffffff"
PANEL    = "#f8f9fa"

class MisionPerfilWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.setup_ui()
        self.procesar_mision()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Calculando Perfil de Misión Dinámico 24h...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        self.main_layout.addWidget(self.status_label)
        
        # Figure
        self.figure = Figure(figsize=(12, 10), dpi=100)
        self.figure.patch.set_facecolor(BG)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.canvas)
        
    def procesar_mision(self):
        try:
            self.figure.clear()
            
            # 1. PARÁMETROS DINÁMICOS
            vel_df = self.data_loader.get_velocidades_data() if hasattr(self.data_loader, 'get_velocidades_data') else None
            Vc = 41.77
            if vel_df is not None and not vel_df.empty:
                if 'V_cruise (m/s)' in vel_df.columns:
                    Vc = vel_df['V_cruise (m/s)'].mean()

            alt_ceil_m = UAVConstants.MAX_ALTITUDE_M
            alt_floor_m = 15000.0
            alt_ceil = alt_ceil_m / 1000.0  # en km
            alt_floor = alt_floor_m / 1000.0 # en km
            
            # Dinámica del Planeo
            L_D = 35.0  # Asumimos una fineza de 35 (Typical HALE UAV)
            sink_rate = Vc / L_D # m/s (aproximación para ángulos pequeños)
            
            delta_alt = alt_ceil_m - alt_floor_m # 10000 m
            glide_time_sec = delta_alt / sink_rate
            glide_time_hrs = glide_time_sec / 3600.0
            
            t_sunrise = 6.0
            t_sunset = 18.0
            t_glide_end = t_sunset + glide_time_hrs
            
            # Limitar si planea más allá de la medianoche
            if t_glide_end > 24.0:
                t_glide_end = 24.0
            
            soc_minimo = 20.0
            
            # Fases
            t1 = np.linspace(0, t_sunrise, 50)
            h1 = np.full_like(t1, alt_floor)
            soc1 = np.linspace(60, soc_minimo, 50) 
            
            t_climb_end = 9.0
            t2 = np.linspace(t_sunrise, t_climb_end, 50)
            h2 = np.linspace(alt_floor, alt_ceil, 50)
            soc2 = np.linspace(soc_minimo, 45, 50) 
            
            t3 = np.linspace(t_climb_end, t_sunset, 100)
            h3 = np.full_like(t3, alt_ceil)
            soc3 = np.clip(np.linspace(45, 120, 100), a_min=None, a_max=100) 
            
            t4 = np.linspace(t_sunset, t_glide_end, 50)
            h4 = np.linspace(alt_ceil, alt_floor, 50)
            soc4 = np.linspace(100, 96, 50) # Solo aviónica
            
            t5 = np.linspace(t_glide_end, 24, 50)
            h5 = np.full_like(t5, alt_floor)
            soc5 = np.linspace(96, 60, 50) 
            
            time = np.concatenate([t1, t2, t3, t4, t5])
            altitude = np.concatenate([h1, h2, h3, h4, h5])
            soc = np.concatenate([soc1, soc2, soc3, soc4, soc5])
            
            # 2. GRAFICACIÓN DUAL
            ax1 = self.figure.add_subplot(211)
            ax2 = self.figure.add_subplot(212, sharex=ax1)
            
            # --- PANEL 1: ALTITUD ---
            ax1.axvspan(0, t_sunrise, color='#1a1a2e', alpha=0.15)
            ax1.axvspan(t_sunrise, t_sunset, color='#fce38a', alpha=0.15)
            ax1.axvspan(t_sunset, 24, color='#1a1a2e', alpha=0.15)
            
            ax1.plot(time, altitude, color='#1f2937', linewidth=3, label='Perfil de Vuelo')
            
            ax1.text((t_climb_end + t_sunset)/2, alt_ceil + 0.5, f'Crucero Diurno ({alt_ceil} km)', ha='center', fontsize=10, style='italic', color='#1f2937')
            ax1.text(t_sunrise/2, alt_floor + 0.5, f'Vuelo Nocturno ({alt_floor} km)', ha='center', fontsize=10, style='italic', color='#1f2937')
            ax1.text((t_sunset + t_glide_end)/2, (alt_ceil + alt_floor)/2 + 1, f'Planeo Libre\n(Motor OFF)\n{glide_time_hrs:.2f} hrs', ha='center', fontsize=9, color='#0284c7', fontweight='bold')
            
            ax1.set_ylabel('Altitud (km)', fontweight='bold')
            ax1.set_title(f'Perfil de Misión 24h: Planeo calculado a L/D={L_D:.1f}', pad=15, fontsize=14, fontweight='bold', color='#2C3E50')
            ax1.set_ylim(alt_floor - 2, alt_ceil + 3)
            ax1.grid(True, alpha=0.3, linestyle='--')
            ax1.legend(loc='upper left')
            
            # --- PANEL 2: SoC ---
            ax2.axvspan(0, t_sunrise, color='#1a1a2e', alpha=0.15)
            ax2.axvspan(t_sunrise, t_sunset, color='#fce38a', alpha=0.15)
            ax2.axvspan(t_sunset, 24, color='#1a1a2e', alpha=0.15)
            
            ax2.plot(time, soc, color='#10b981', linewidth=3, label='Estado de Carga (SoC)')
            ax2.fill_between(time, soc_minimo, soc, where=(soc >= soc_minimo), color='#10b981', alpha=0.2)
            
            ax2.axhspan(0, soc_minimo, color='#ef4444', alpha=0.2)
            ax2.axhline(soc_minimo, color='#dc2626', linestyle='--', linewidth=2, label=f'Límite Seguridad ({soc_minimo}%)')
            
            ax2.text(12, 60, 'Margen\nOperativo Útil', ha='center', color='#059669', fontweight='bold', fontsize=10)
            ax2.text(12, 10, 'Zona Restringida\n(Degradación Química)', ha='center', color='#991b1b', fontweight='bold', fontsize=10)
            
            ax2.set_xlabel('Hora del Día (h)', fontweight='bold')
            ax2.set_ylabel('Nivel de Batería (%)', fontweight='bold')
            ax2.set_ylim(0, 110)
            ax2.set_xlim(0, 24)
            ax2.set_xticks(np.arange(0, 25, 2))
            ax2.legend(loc='upper left')
            ax2.grid(True, alpha=0.3, linestyle='--')
            
            for ax in [ax1, ax2]:
                ax.axvline(t_sunrise, color='#f59e0b', linestyle=':', linewidth=2)
                ax.axvline(t_sunset, color='#f59e0b', linestyle=':', linewidth=2)
                ax.axvline(t_glide_end, color='#0ea5e9', linestyle=':', linewidth=2)
                
            self.figure.tight_layout()
            self.canvas.draw()
            
            self.status_label.setText(f"Planeo Dinámico Calculado: {glide_time_hrs:.2f} Horas de Motores Apagados ahorradas.")
            self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            self.status_label.setText(f"Error generando Perfil de Misión: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.figure.tight_layout()
        self.canvas.draw_idle()
