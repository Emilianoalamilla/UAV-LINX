# module_rendimiento_avanzado.py
import numpy as np
import matplotlib
matplotlib.use('QtAgg')
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
import math
from core.globals import UAVConstants

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
WHITE    = "#1f2937" # Dark text on white BG
ACCENT   = "#22d3ee"

def title_bar(ax, title, color=TEAL):
    ax.set_facecolor(PANEL)
    ax.set_title(title, color=color, fontsize=11, fontweight="bold", pad=8, loc="left")

class RendimientoAvanzadoWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.setup_ui()
        self.procesar_rendimiento()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Calculando Rendimiento Avanzado y Superficies...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        self.main_layout.addWidget(self.status_label)
        
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Tabs container
        self.figures = []
        self.canvases = []
        
        tab_names = ["1. Planform Ala Recta", "2. Dimensionamiento Flaps", "3. Dimensionamiento Alerones", "4. Diagrama V-n y Vuelo", "5. Superficies y Batería"]
        
        for name in tab_names:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            fig = Figure(figsize=(12, 7), dpi=100)
            fig.patch.set_facecolor(BG)
            canvas = FigureCanvas(fig)
            toolbar = NavigationToolbar(canvas, self)
            layout.addWidget(toolbar)
            layout.addWidget(canvas)
            self.tabs.addTab(tab, name)
            
            self.figures.append(fig)
            self.canvases.append(canvas)

    def rotate(self, x, y, x0, y0, angle):
        dx, dy = x - x0, y - y0
        xr = x0 + dx*np.cos(angle) - dy*np.sin(angle)
        yr = y0 + dx*np.sin(angle) + dy*np.cos(angle)
        return xr, yr

    def procesar_rendimiento(self):
        try:
            # --- CASCADA DE DATOS (HALE UAV) ---
            b = UAVConstants.WINGSPAN_M if hasattr(UAVConstants, 'WINGSPAN_M') else 15.5
            S_ala = UAVConstants.SURFACE_AREA
            c_const = S_ala / b
            cr = c_const
            ct = c_const
            semi_b = b / 2
            
            # Dinámica
            V_max = 60.0
            V_stall = 15.0
            Vc = 41.77
                
            # Control Surfaces Setup
            flap_eta_in  = 0.10   
            flap_eta_out = 0.65   
            flap_cf_frac = 0.25
            
            ail_eta_in  = 0.65
            ail_eta_out = 0.95
            ail_cf_frac = 0.22
            
            S_flap_max = 2 * ((flap_eta_out - flap_eta_in)*semi_b) * (flap_cf_frac * c_const)
            S_flap_min = S_flap_max * 0.8
            S_aileron = 2 * ((ail_eta_out - ail_eta_in)*semi_b) * (ail_cf_frac * c_const)
            
            def chord_at(eta): return c_const

            # ==========================================
            # TAB 1: PLANFORM ALA RECTA
            # ==========================================
            fig1 = self.figures[0]
            fig1.clear()
            ax1 = fig1.add_subplot(111)
            ax1.set_facecolor(BG)
            fig1.suptitle("PLANFORM DEL ALA RECTA — Flaps y Alerones", color=CYAN, fontsize=15, fontweight="bold", y=0.97)

            def draw_surface(ax, eta_in, eta_out, cf_frac, color, label, sign=1, alpha=0.7):
                etas = np.linspace(eta_in, eta_out, 30)
                y = etas * semi_b * sign
                le = np.zeros_like(etas)
                c = np.ones_like(etas) * c_const
                te = le + c
                hinge = te - cf_frac * c
                xs = np.concatenate([hinge, te[::-1]])
                ys = np.concatenate([y, y[::-1]])
                ax.fill(xs, ys, color=color, alpha=alpha, zorder=6)
                ax.plot(xs, ys, color=color, lw=1.5, zorder=7)
                x_mid = c_const - (cf_frac / 2) * c_const
                y_mid = (eta_in + eta_out) / 2 * semi_b * sign
                ax.text(x_mid, y_mid, label, color="white", fontsize=8, ha="center", va="center", fontweight="bold", zorder=10)

            def wing_contour(mirror=False):
                etas = np.linspace(0, 1, 60)
                y = etas * semi_b
                le = np.zeros_like(etas)
                c = np.ones_like(etas) * c_const
                te = le + c
                xs = np.concatenate([le, te[::-1]])
                ys = np.concatenate([y, y[::-1]])
                if mirror: ys = -ys
                return xs, ys

            for sign in [1, -1]:
                xs, ys = wing_contour(mirror=(sign == -1))
                ax1.fill(xs, ys, color="#1e3a5f", alpha=0.85, zorder=2)
                ax1.plot(xs, ys, color=TEAL, lw=1.0, zorder=3)
                
            fus_w = 0.8
            fus_l = c_const * 2.5
            ell = patches.Ellipse((c_const/2, 0), fus_l, fus_w, facecolor="#263040", edgecolor=LTGRAY, linewidth=1.2, zorder=5)
            ax1.add_patch(ell)
            
            for s in [1, -1]:
                draw_surface(ax1, flap_eta_in, flap_eta_out, flap_cf_frac, GREEN, "FLAP", sign=s)
                draw_surface(ax1, ail_eta_in, ail_eta_out, ail_cf_frac, RED, "ALERÓN", sign=s)
                
            ax1.set_xlabel("Cuerda [m]")
            ax1.set_ylabel("Envergadura [m]")
            ax1.set_aspect("equal")
            ax1.grid(True, alpha=0.2)
            fig1.tight_layout()

            # ==========================================
            # TAB 2: DIMENSIONAMIENTO DE FLAPS
            # ==========================================
            fig2 = self.figures[1]
            fig2.clear()
            fig2.suptitle("DIMENSIONAMIENTO DE FLAPS", color=CYAN, fontsize=15, fontweight="bold", y=0.97)
            gs2 = gridspec.GridSpec(2, 2, figure=fig2, hspace=0.3, wspace=0.3)
            
            ax2a = fig2.add_subplot(gs2[0, 0])
            title_bar(ax2a, "Superficie vs Deflexión", GREEN)
            deflexiones = np.array([0, 5, 10, 15, 20, 25, 30, 35, 40])
            S_flap_defl = np.interp(deflexiones, [5, 40], [S_flap_min, S_flap_max])
            S_flap_defl[0] = 0
            ax2a.plot(deflexiones, S_flap_defl, color=GREEN, lw=2.5, marker="o")
            ax2a.set_xlabel("Deflexión δ_f [°]")
            ax2a.set_ylabel("S_flap [m²]")
            ax2a.grid(True, alpha=0.3)

            ax2b = fig2.add_subplot(gs2[0, 1])
            title_bar(ax2b, "Cuerda de Flap vs Envergadura", GREEN)
            etas = np.linspace(0, 1, 200)
            flap_chord = flap_cf_frac * c_const * np.ones_like(etas)
            y_span = etas * semi_b
            mask_flap = (etas >= flap_eta_in) & (etas <= flap_eta_out)
            ax2b.fill_between(y_span[mask_flap], flap_chord[mask_flap], color=GREEN, alpha=0.5)
            ax2b.plot(y_span[mask_flap], flap_chord[mask_flap], color=GREEN, lw=2.5)
            ax2b.set_xlabel("Semi-envergadura [m]")
            ax2b.set_ylabel("Cuerda [m]")
            ax2b.grid(True, alpha=0.3)

            ax2d = fig2.add_subplot(gs2[1, :])
            title_bar(ax2d, "Sección Transversal: Perfil + Flap deflectado a 30°", TEAL)
            xp = np.linspace(0, 1, 100)
            yup  =  0.12 * (0.2969*np.sqrt(xp) - 0.1260*xp - 0.3516*xp**2 + 0.2843*xp**3 - 0.1015*xp**4)
            ylow = -yup
            cut = 1 - flap_cf_frac
            mask_p = xp <= cut
            ax2d.fill_between(xp[mask_p], yup[mask_p], ylow[mask_p], color="#1a3f6f", alpha=0.9)
            
            delta = np.radians(30)
            xf_raw = np.linspace(cut, 1, 40)
            yf_up  =  0.08 * (0.2969*np.sqrt(xf_raw) - 0.1260*xf_raw)
            yf_low = -yf_up
            xfu, yfu = self.rotate(xf_raw, yf_up, cut, 0, delta)
            xfl, yfl = self.rotate(xf_raw, yf_low, cut, 0, delta)
            ax2d.fill(np.concatenate([xfu, xfl[::-1]]), np.concatenate([yfu, yfl[::-1]]), color=GREEN, alpha=0.75)
            ax2d.set_xlim(-0.05, 1.25)
            ax2d.set_ylim(-0.2, 0.22)
            ax2d.set_aspect("equal")
            ax2d.grid(True, alpha=0.2)
            fig2.tight_layout()

            # ==========================================
            # TAB 3: DIMENSIONAMIENTO DE ALERONES
            # ==========================================
            fig3 = self.figures[2]
            fig3.clear()
            fig3.suptitle("DIMENSIONAMIENTO DE ALERONES", color=RED, fontsize=15, fontweight="bold", y=0.97)
            gs3 = gridspec.GridSpec(1, 2, figure=fig3, wspace=0.3)
            
            ax3a = fig3.add_subplot(gs3[0, 0])
            title_bar(ax3a, "Zonas de Control", RED)
            chord_normalized = np.ones_like(etas)
            mask_ail  = (etas >= ail_eta_in)  & (etas <= ail_eta_out)
            ax3a.fill_between(y_span, chord_normalized, 0, where=mask_flap, color=GREEN, alpha=0.4, label="Zona Flap")
            ax3a.fill_between(y_span, chord_normalized, 0, where=mask_ail,  color=RED,   alpha=0.5, label="Zona Alerón")
            ax3a.plot(y_span, chord_normalized, color=TEAL, lw=2)
            ax3a.set_xlabel("Semi-envergadura [m]")
            ax3a.legend()
            ax3a.grid(True, alpha=0.3)

            ax3c = fig3.add_subplot(gs3[0, 1])
            title_bar(ax3c, "Alerón ↑ (−20°) y Alerón ↓ (+20°)", ACCENT)
            def draw_aileron_section(ax, x_offset, delta_deg, color, label):
                cut = 1 - ail_cf_frac
                mask_p = xp <= cut
                ax.fill_between(xp[mask_p] + x_offset, yup[mask_p], ylow[mask_p], color="#1a3f6f", alpha=0.85)
                delta = np.radians(delta_deg)
                xf_raw = np.linspace(cut, 1, 40)
                yf_up  =  0.08 * (0.2969*np.sqrt(np.clip(xf_raw, 1e-8, None)))
                yf_low = -yf_up
                xfu, yfu = self.rotate(xf_raw, yf_up, cut, 0, delta)
                xfl, yfl = self.rotate(xf_raw, yf_low, cut, 0, delta)
                ax.fill(np.concatenate([xfu, xfl[::-1]]) + x_offset, np.concatenate([yfu, yfl[::-1]]), color=color, alpha=0.75)
                ax.text(x_offset + 0.5, -0.18, label, ha="center", color=color, fontsize=9, fontweight="bold")

            draw_aileron_section(ax3c, 0.0,  -20, CYAN,  "Alerón ↑  (−20°)")
            draw_aileron_section(ax3c, 1.3,  +20, RED,   "Alerón ↓  (+20°)")
            ax3c.set_xlim(-0.1, 2.5)
            ax3c.set_ylim(-0.25, 0.25)
            ax3c.set_aspect("equal")
            ax3c.grid(True, alpha=0.2)
            fig3.tight_layout()

            # ==========================================
            # TAB 4: DIAGRAMA V-n (Adaptado para HALE UAV)
            # ==========================================
            fig4 = self.figures[3]
            fig4.clear()
            fig4.suptitle("DIAGRAMA V-n Y PERFIL DE MISIÓN", color=GOLD, fontsize=15, fontweight="bold", y=0.97)
            gs4 = gridspec.GridSpec(1, 2, figure=fig4, wspace=0.3)
            
            ax4c = fig4.add_subplot(gs4[0, 0])
            title_bar(ax4c, "Diagrama V-n (Estructural HALE UAV)", PURPLE)
            n_max = 2.0  # Ajustado para UAV ligero
            n_min = -1.0 # Ajustado para UAV ligero
            V_arr = np.linspace(0, V_max * 1.05, 300)
            
            # Límites aerodinámicos
            n_pos = np.minimum((V_arr / V_stall) ** 2, n_max)
            n_neg = np.maximum(-0.5 * (V_arr / V_stall) ** 2, n_min)
            
            ax4c.fill_between(V_arr, n_neg, n_pos, where=(V_arr <= V_max), color=PURPLE, alpha=0.2)
            ax4c.plot(V_arr[V_arr <= V_max], n_pos[V_arr <= V_max], color=GOLD, lw=2, label="n+ (Sustentación Max)")
            ax4c.plot(V_arr[V_arr <= V_max], n_neg[V_arr <= V_max], color=TEAL, lw=2, label="n− (Sustentación Min)")
            ax4c.axhline(n_max, color=RED,  ls="--", lw=1.5, label=f"n_lím = {n_max}")
            ax4c.axhline(n_min, color=CYAN, ls="--", lw=1.5, label=f"n_mín = {n_min}")
            ax4c.axvline(Vc,    color=GREEN, ls=":", lw=1.5, label=f"Vc = {Vc:.1f} m/s")
            ax4c.axvline(V_max,  color=RED,   ls=":", lw=1.5, label=f"Vmax = {V_max:.1f} m/s")
            
            ax4c.set_xlabel("Velocidad Equivalente (EAS) [m/s]")
            ax4c.set_ylabel("Factor de carga n [-]")
            ax4c.set_xlim(0, V_max * 1.1)
            ax4c.set_ylim(n_min * 1.4, n_max * 1.3)
            ax4c.legend(fontsize=8)
            ax4c.grid(True, alpha=0.3)
            
            # Dinámica de Viraje (Basada en tu script Matlab)
            ax4a = fig4.add_subplot(gs4[0, 1])
            title_bar(ax4a, "Dinámica de Vuelo (Crucero)", GOLD)
            g = 9.81
            phi_rad = math.radians(5.0) # 5 grados bank angle
            R_viraje = Vc**2 / (g * math.tan(phi_rad))
            omega = Vc / R_viraje
            
            bar_names = ["Velocidad Crucero", "Velocidad Stall", "Radio Viraje (Bank 5°)", "Tasa Giro (omega)"]
            bar_vals = [Vc, V_stall, R_viraje, omega*100] # Escalar omega visualmente
            bars4 = ax4a.barh(np.arange(len(bar_names)), bar_vals, color=[GREEN, RED, GOLD, TEAL], height=0.5)
            ax4a.set_yticks(np.arange(len(bar_names)))
            ax4a.set_yticklabels(bar_names)
            
            for i, val in enumerate(bar_vals):
                label = f"{val:.2f} m/s" if i<2 else (f"{val:.0f} m" if i==2 else f"{val/100:.3f} rad/s")
                ax4a.text(val + 0.5, i, label, va='center', fontweight='bold', color=WHITE)
                
            ax4a.grid(True, axis="x", alpha=0.3)
            fig4.tight_layout()

            # ==========================================
            # TAB 5: SUPERFICIES Y BATERÍA (Electric Endurance)
            # ==========================================
            fig5 = self.figures[4]
            fig5.clear()
            fig5.suptitle("SUPERFICIES Y BALANCE ENERGÉTICO (BATERÍA)", color=PURPLE, fontsize=15, fontweight="bold", y=0.97)
            gs5 = gridspec.GridSpec(2, 2, figure=fig5, hspace=0.3, wspace=0.3)
            
            # Superficies
            ax5b = fig5.add_subplot(gs5[0, 0])
            title_bar(ax5b, "Proporción del Ala Total", PURPLE)
            S_ht = S_ala * 0.15
            S_vt = S_ala * 0.08
            pie_labels = ["Resto Ala", "Flaps", "Alerones", "Est. Horiz", "Est. Vert"]
            pie_vals = [S_ala - S_flap_max - S_aileron, S_flap_max, S_aileron, S_ht, S_vt]
            ax5b.pie(pie_vals, labels=pie_labels, colors=[CYAN, GREEN, RED, TEAL, GOLD], autopct="%1.1f%%", startangle=140)
            
            # Pesos HALE (Eléctrico)
            ax5d = fig5.add_subplot(gs5[0, 1])
            title_bar(ax5d, "Distribución de Pesos (HALE Eléctrico)", CYAN)
            W_total = UAVConstants.WEIGHT_N / 9.81
            W_batt = W_total * 0.40 # 40% peso en batería
            W_struct = W_total * 0.50
            W_payload = W_total * 0.10
            ax5d.bar(["Baterías", "Estructura", "Payload"], [W_batt, W_struct, W_payload], color=[GREEN, GRAY, GOLD])
            ax5d.set_ylabel("Masa [kg]")
            ax5d.grid(True, axis='y')
            
            # SoC vs Time Simulation (Batería simulando Crucero Diurno)
            ax5e = fig5.add_subplot(gs5[1, :])
            title_bar(ax5e, "Telemetría de Misión: Estado de Carga Batería (SoC) en Crucero Diurno", GREEN)
            t_min = np.linspace(0, 30, 100) # 30 minutos
            soc = np.linspace(40, 65, 100) # Carga solar desde 40% a 65% como tu script
            ax5e.plot(t_min, soc, color=GREEN, lw=3, label="SoC Batería")
            ax5e.fill_between(t_min, soc, 0, color=GREEN, alpha=0.2)
            ax5e.set_ylim(0, 100)
            ax5e.set_xlabel("Tiempo de Misión [min]")
            ax5e.set_ylabel("SoC [%]")
            ax5e.legend()
            ax5e.grid(True, alpha=0.3)
            
            fig5.tight_layout()
            
            # Render All
            for canvas in self.canvases:
                canvas.draw()
                
            self.status_label.setText(f"Cálculos exitosos: V_stall={V_stall:.2f}m/s, n_max={n_max}, Vc={Vc:.2f}m/s")
            self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            self.status_label.setText(f"Error generando gráficas avanzadas: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        for fig, canvas in zip(self.figures, self.canvases):
            fig.tight_layout()
            canvas.draw_idle()
