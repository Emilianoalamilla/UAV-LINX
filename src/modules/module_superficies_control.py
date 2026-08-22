# module_superficies_control.py
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from core.globals import UAVConstants

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
import mplcursors

# PALETA DE COLORES
BG       = "#ffffff"
PANEL    = "#f8f9fa"
CYAN     = "#00d4ff"
TEAL     = "#0ea5e9"
GOLD     = "#f59e0b"
GREEN    = "#10b981"
RED      = "#ef4444"
PURPLE   = "#8b5cf6"
GRAY     = "#374151"
LTGRAY   = "#6b7280"
WHITE    = "#1f2937"
ACCENT   = "#22d3ee"

def title_bar(ax, title, color=TEAL):
    ax.set_facecolor(PANEL)
    ax.set_title(title, color=color, fontsize=11, fontweight="bold", pad=8, loc="left")

class SuperficiesControlWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.setup_ui()
        self.procesar_superficies()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Calculando Superficies de Control (Flaps y Alerones)...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        self.main_layout.addWidget(self.status_label)
        
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Tab 1: Planform
        self.tab_plan = QWidget()
        self.layout_plan = QVBoxLayout(self.tab_plan)
        self.fig_plan = Figure(figsize=(12, 6), dpi=100)
        self.fig_plan.patch.set_facecolor(BG)
        self.canvas_plan = FigureCanvas(self.fig_plan)
        self.toolbar_plan = NavigationToolbar(self.canvas_plan, self)
        self.layout_plan.addWidget(self.toolbar_plan)
        self.layout_plan.addWidget(self.canvas_plan)
        self.tabs.addTab(self.tab_plan, "Planform del Ala")
        
        # Tab 2: Flaps
        self.tab_flaps = QWidget()
        self.layout_flaps = QVBoxLayout(self.tab_flaps)
        self.fig_flaps = Figure(figsize=(12, 6), dpi=100)
        self.fig_flaps.patch.set_facecolor(BG)
        self.canvas_flaps = FigureCanvas(self.fig_flaps)
        self.toolbar_flaps = NavigationToolbar(self.canvas_flaps, self)
        self.layout_flaps.addWidget(self.toolbar_flaps)
        self.layout_flaps.addWidget(self.canvas_flaps)
        self.tabs.addTab(self.tab_flaps, "Flaps")
        
        # Tab 3: Alerones
        self.tab_ailerons = QWidget()
        self.layout_ailerons = QVBoxLayout(self.tab_ailerons)
        self.fig_ailerons = Figure(figsize=(12, 6), dpi=100)
        self.fig_ailerons.patch.set_facecolor(BG)
        self.canvas_ailerons = FigureCanvas(self.fig_ailerons)
        self.toolbar_ailerons = NavigationToolbar(self.canvas_ailerons, self)
        self.layout_ailerons.addWidget(self.toolbar_ailerons)
        self.layout_ailerons.addWidget(self.canvas_ailerons)
        self.tabs.addTab(self.tab_ailerons, "Alerones")

    def procesar_superficies(self):
        try:
            # Parámetros HALE UAV
            S_ala = UAVConstants.SURFACE_AREA
            b = UAVConstants.WINGSPAN_M if hasattr(UAVConstants, 'WINGSPAN_M') else 15.5
            cr = S_ala / b
            ct = cr  # Ala rectangular
            semi_b = b / 2
            
            flap_eta_in  = 0.10   
            flap_eta_out = 0.65   
            flap_cf_frac = 0.25   
            
            ail_eta_in  = 0.65
            ail_eta_out = 0.95
            ail_cf_frac = 0.22
            
            def chord_at(eta):
                return cr + (ct - cr) * eta

            # ---------------------------------------------------------
            # TAB 1: PLANFORM
            # ---------------------------------------------------------
            self.fig_plan.clear()
            ax1 = self.fig_plan.add_subplot(111)
            ax1.set_facecolor(BG)
            
            def draw_surface(ax, eta_in, eta_out, cf_frac, color, label, sign=1, alpha=0.7):
                etas = np.linspace(eta_in, eta_out, 30)
                y    = etas * semi_b * sign
                le   = 0.25 * (cr - ct) * etas
                c    = np.array([chord_at(e) for e in etas])
                te   = le + c
                hinge= te - cf_frac * c
                xs = np.concatenate([hinge, te[::-1]])
                ys = np.concatenate([y, y[::-1]])
                ax.fill(xs, ys, color=color, alpha=alpha, zorder=6)
                ax.plot(xs, ys, color=color, lw=1.5, zorder=7)
                eta_mid = (eta_in + eta_out) / 2
                x_mid = (le[15] + c[15]) - (cf_frac / 2) * c[15]
                ax.text(x_mid, eta_mid * semi_b * sign, label, color="white", fontsize=8, ha="center", va="center", fontweight="bold", zorder=10)

            def wing_contour(mirror=False):
                etas = np.linspace(0, 1, 60)
                y = etas * semi_b
                le = 0.25 * (cr - ct) * etas
                c  = np.array([chord_at(e) for e in etas])
                te = le + c
                xs = np.concatenate([le, te[::-1]])
                ys = np.concatenate([y,  y[::-1]])
                if mirror: ys = -ys
                return xs, ys

            for sign in [1, -1]:
                xs, ys = wing_contour(mirror=(sign == -1))
                ax1.fill(xs, ys, color="#1e3a5f", alpha=0.85, zorder=2)
                ax1.plot(xs, ys, color=TEAL, lw=1.0, zorder=3)
                
            fus_w = 0.8
            fus_l = cr * 3.0
            ell = patches.Ellipse((fus_l / 3, 0), fus_l, fus_w, facecolor="#263040", edgecolor=LTGRAY, linewidth=1.2, zorder=5)
            ax1.add_patch(ell)
            
            for s in [1, -1]:
                draw_surface(ax1, flap_eta_in, flap_eta_out, flap_cf_frac, GREEN, "FLAP", sign=s)
                draw_surface(ax1, ail_eta_in, ail_eta_out, ail_cf_frac, RED, "ALERÓN", sign=s)
                
            ax1.set_xlabel("Cuerda [m]", color=WHITE)
            ax1.set_ylabel("Envergadura [m]", color=WHITE)
            ax1.set_aspect("equal")
            ax1.set_title("Planform del Ala (HALE UAV)", color=TEAL, fontsize=14, fontweight="bold")
            ax1.grid(True, alpha=0.2)
            
            self.fig_plan.tight_layout()
            self.canvas_plan.draw()

            # ---------------------------------------------------------
            # TAB 2: FLAPS
            # ---------------------------------------------------------
            self.fig_flaps.clear()
            gs2 = gridspec.GridSpec(1, 2, figure=self.fig_flaps, wspace=0.3)
            
            ax2b = self.fig_flaps.add_subplot(gs2[0, 0])
            title_bar(ax2b, "Cuerda de Flap vs Envergadura", GREEN)
            etas = np.linspace(0, 1, 200)
            chord_local = cr + (ct - cr) * etas
            flap_chord  = flap_cf_frac * chord_local
            y_span = etas * semi_b
            mask_flap = (etas >= flap_eta_in) & (etas <= flap_eta_out)
            
            ax2b.plot(y_span, flap_chord, color=LTGRAY, lw=1, ls=":", label="Potencial máx")
            ax2b.fill_between(y_span[mask_flap], flap_chord[mask_flap], color=GREEN, alpha=0.5, label="Zona de flap")
            ax2b.plot(y_span[mask_flap], flap_chord[mask_flap], color=GREEN, lw=2.5)
            ax2b.axvline(flap_eta_in * semi_b,  color=GOLD, ls="--", lw=1, alpha=0.8)
            ax2b.axvline(flap_eta_out * semi_b, color=GOLD, ls="--", lw=1, alpha=0.8)
            ax2b.set_xlabel("Posición en semi-envergadura [m]")
            ax2b.set_ylabel("Cuerda del flap [m]")
            ax2b.legend(fontsize=9)
            ax2b.grid(True, alpha=0.3)
            
            ax2d = self.fig_flaps.add_subplot(gs2[0, 1])
            title_bar(ax2d, "Sección Transversal: Perfil + Flap deflectado", TEAL)
            xp = np.linspace(0, 1, 100)
            yup  =  0.12 * (0.2969*np.sqrt(xp) - 0.1260*xp - 0.3516*xp**2 + 0.2843*xp**3 - 0.1015*xp**4)
            ylow = -0.12 * (0.2969*np.sqrt(xp) - 0.1260*xp - 0.3516*xp**2 + 0.2843*xp**3 - 0.1015*xp**4)
            cut = 1 - flap_cf_frac
            mask_p = xp <= cut
            ax2d.fill_between(xp[mask_p], yup[mask_p], ylow[mask_p], color="#1a3f6f", alpha=0.9, zorder=3)
            
            delta = np.radians(30)
            xf_raw = np.linspace(cut, 1, 40)
            yf_up  =  0.08 * (0.2969*np.sqrt(xf_raw) - 0.1260*xf_raw)
            yf_low = -0.08 * (0.2969*np.sqrt(xf_raw) - 0.1260*xf_raw)
            
            def rotate(x, y, x0, y0, angle):
                dx, dy = x - x0, y - y0
                return x0 + dx*np.cos(angle) - dy*np.sin(angle), y0 + dx*np.sin(angle) + dy*np.cos(angle)

            xfu, yfu = rotate(xf_raw, yf_up, cut, 0, delta)
            xfl, yfl = rotate(xf_raw, yf_low, cut, 0, delta)
            ax2d.fill(np.concatenate([xfu, xfl[::-1]]), np.concatenate([yfu, yfl[::-1]]), color=GREEN, alpha=0.75, zorder=5)
            ax2d.plot(xfu, yfu, color=GREEN, lw=2, zorder=6)
            ax2d.plot(xfl, yfl, color=GREEN, lw=2, zorder=6)
            
            ax2d.set_xlim(-0.05, 1.25)
            ax2d.set_ylim(-0.2, 0.22)
            ax2d.set_aspect("equal")
            ax2d.grid(True, alpha=0.2)
            
            self.fig_flaps.tight_layout()
            self.canvas_flaps.draw()

            # ---------------------------------------------------------
            # TAB 3: ALERONES
            # ---------------------------------------------------------
            self.fig_ailerons.clear()
            gs3 = gridspec.GridSpec(1, 2, figure=self.fig_ailerons, wspace=0.3)
            
            ax3a = self.fig_ailerons.add_subplot(gs3[0, 0])
            title_bar(ax3a, "Distribución de Cuerda y Zonas de Control", RED)
            chord_normalized = chord_local / cr
            mask_ail  = (etas >= ail_eta_in)  & (etas <= ail_eta_out)
            ax3a.fill_between(y_span, chord_normalized, 0, where=mask_flap, color=GREEN, alpha=0.4, label="Flap")
            ax3a.fill_between(y_span, chord_normalized, 0, where=mask_ail,  color=RED,   alpha=0.5, label="Alerón")
            ax3a.plot(y_span, chord_normalized, color=TEAL, lw=2)
            ax3a.set_xlabel("Semi-envergadura [m]")
            ax3a.legend()
            ax3a.grid(True, alpha=0.3)
            
            ax3c = self.fig_ailerons.add_subplot(gs3[0, 1])
            title_bar(ax3c, "Alerón ↑ (−20°) y ↓ (+20°)", ACCENT)
            def draw_aileron_section(ax, x_offset, delta_deg, color, label):
                cut = 1 - ail_cf_frac
                mask_p = xp <= cut
                ax.fill_between(xp[mask_p] + x_offset, yup[mask_p], ylow[mask_p], color="#1a3f6f", alpha=0.85, zorder=3)
                delta = np.radians(delta_deg)
                xf_raw = np.linspace(cut, 1, 40)
                yf_up  =  0.08 * (0.2969*np.sqrt(np.clip(xf_raw, 1e-8, None)))
                yf_low = -0.08 * (0.2969*np.sqrt(np.clip(xf_raw, 1e-8, None)))
                xfu, yfu = rotate(xf_raw, yf_up,  cut, 0, delta)
                xfl, yfl = rotate(xf_raw, yf_low, cut, 0, delta)
                ax.fill(np.concatenate([xfu, xfl[::-1]]) + x_offset, np.concatenate([yfu, yfl[::-1]]), color=color, alpha=0.75, zorder=5)
                ax.text(x_offset + 0.5, -0.18, label, ha="center", color=color, fontsize=9, fontweight="bold")

            draw_aileron_section(ax3c, 0.0,  -20, TEAL,  "Alerón ↑  (−20°)")
            draw_aileron_section(ax3c, 1.3,  +20, RED,   "Alerón ↓  (+20°)")
            ax3c.set_xlim(-0.1, 2.5)
            ax3c.set_ylim(-0.25, 0.25)
            ax3c.set_aspect("equal")
            ax3c.grid(True, alpha=0.2)
            
            self.fig_ailerons.tight_layout()
            self.canvas_ailerons.draw()
            
            mplcursors.cursor(hover=True)
            self.status_label.setText("Superficies de Control dimensionadas correctamente.")
            self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            self.status_label.setText(f"Error generando superficies: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fig_plan.tight_layout()
        self.canvas_plan.draw_idle()
        self.fig_flaps.tight_layout()
        self.canvas_flaps.draw_idle()
        self.fig_ailerons.tight_layout()
        self.canvas_ailerons.draw_idle()
