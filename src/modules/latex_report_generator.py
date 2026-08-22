import os
import datetime

def format_matrix(matrix):
    """Convierte una matriz 2D de Python en código de matriz de LaTeX."""
    if not matrix:
        return ""
    rows = []
    for row in matrix:
        # Formato a 4 decimales para cada elemento
        formatted_row = " & ".join(f"{val:.4f}" for val in row)
        rows.append(formatted_row)
    return "\\begin{bmatrix}\n  " + " \\\\\n  ".join(rows) + "\n\\end{bmatrix}"

def format_complex(c):
    """Formatea un número complejo para LaTeX."""
    if isinstance(c, complex):
        sign = "+" if c.imag >= 0 else "-"
        return f"{c.real:.4f} {sign} {abs(c.imag):.4f}i"
    # Si es float o int
    return f"{float(c):.4f}"

def get_status(condition: bool) -> str:
    """Retorna código de color LaTeX basado en la condición."""
    return r"\textcolor{green}{Cumple}" if condition else r"\textcolor{red}{No Cumple}"

def generate_report(results: dict, filepath: str) -> None:
    """
    Genera un archivo .tex completo con el análisis de estabilidad del UAV.
    
    Args:
        results (dict): Diccionario con todos los parámetros geométricos y de estabilidad.
        filepath (str): Ruta completa donde se guardará el archivo .tex.
    """
    doc = []
    
    # --- Preámbulo ---
    doc.append(r"""\documentclass[a4paper,12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath, amssymb, booktabs, geometry, graphicx, float, xcolor, hyperref, fancyhdr}
\geometry{margin=2.5cm}

\pagestyle{fancy}
\fancyhf{}
\rhead{Análisis de Estabilidad}
\lhead{HALE Solar UAV}
\cfoot{\thepage}

\title{\textbf{Análisis de Estabilidad Estática y Dinámica}\\[0.5em] \large HALE Solar UAV}
\author{Generado automáticamente por HALE UAV Sizing App}
\date{\today}

\begin{document}
\maketitle
""")

    # --- Sección 1: Datos de Entrada ---
    doc.append(r"\section{Datos de Entrada}")
    doc.append(r"\begin{table}[H]")
    doc.append(r"\centering")
    doc.append(r"\begin{tabular}{lrlr}")
    doc.append(r"\toprule")
    doc.append(r"\textbf{Parámetro} & \textbf{Valor} & \textbf{Parámetro} & \textbf{Valor} \\")
    doc.append(r"\midrule")
    doc.append(f"Área Alar ($S_w$) & {results.get('S_w', 0):.2f} m$^2$ & Masa ($m$) & {results.get('m', 0):.2f} kg \\\\")
    doc.append(f"Envergadura ($b$) & {results.get('b', 0):.2f} m & Peso ($W$) & {results.get('W', 0):.2f} N \\\\")
    doc.append(f"Cuerda Media ($\\bar{{c}}$) & {results.get('c_bar', 0):.2f} m & Densidad ($\\rho$) & {results.get('rho', 0):.4f} kg/m$^3$ \\\\")
    doc.append(f"Alargamiento ($AR$) & {results.get('AR', 0):.2f} & Vel. Referencia ($u_0$) & {results.get('u0', 0):.2f} m/s \\\\")
    doc.append(f"Área Cola Horiz. ($S_h$) & {results.get('S_h', 0):.2f} m$^2$ & Posición CG ($x_{{cg}}$) & {results.get('x_cg', 0):.4f} $\\bar{{c}}$ \\\\")
    doc.append(f"Brazo Cola Horiz. ($l_h$) & {results.get('l_h', 0):.2f} m & Posición CA ($x_{{ac}}$) & {results.get('x_ac', 0):.4f} $\\bar{{c}}$ \\\\")
    doc.append(f"Área Cola Vert. ($S_v$) & {results.get('S_v', 0):.2f} m$^2$ & Eficiencia Cola H. ($\\eta_h$) & {results.get('eta_h', 0):.2f} \\\\")
    doc.append(f"Brazo Cola Vert. ($l_v$) & {results.get('l_v', 0):.2f} m & Eficiencia Cola V. ($\\eta_v$) & {results.get('eta_v', 0):.2f} \\\\")
    doc.append(f"Diedro ($\\Gamma$) & {results.get('Gamma_deg', 0):.2f}$^\\circ$ & & \\\\")
    doc.append(r"\bottomrule")
    doc.append(r"\end{tabular}")
    doc.append(r"\end{table}")

    # --- Sección 2: Estabilidad Longitudinal (Estática) ---
    doc.append(r"\section{Estabilidad Longitudinal (Estática)}")

    # V_H
    doc.append(r"\subsection{Coeficiente de Volumen de Cola Horizontal ($V_H$)}")
    doc.append(r"\begin{equation}")
    doc.append(r"  V_H = \frac{S_h \cdot l_h}{S_w \cdot \bar{c}}")
    doc.append(r"\end{equation}")
    doc.append(r"Sustituyendo valores:")
    doc.append(r"\[")
    doc.append(f"  V_H = \\frac{{{results.get('S_h', 0):.2f} \\times {results.get('l_h', 0):.2f}}}{{{results.get('S_w', 0):.2f} \\times {results.get('c_bar', 0):.2f}}} = \\boxed{{{results.get('V_H', 0):.4f}}}")
    doc.append(r"\]")

    # CL_alpha
    doc.append(r"\subsection{Gradiente de Sustentación del Ala ($C_{L_\alpha}$)}")
    doc.append(r"El gradiente de sustentación del ala se obtiene a partir de regresión lineal de datos aerodinámicos de vuelo o estimaciones:")
    doc.append(r"\[")
    doc.append(f"  C_{{L_\\alpha}} = \\boxed{{{results.get('CL_alpha', 0):.4f}}} \\text{{ rad}}^{{-1}}")
    doc.append(r"\]")

    # CL_alpha_h
    doc.append(r"\subsection{Gradiente de Sustentación de la Cola Horizontal ($C_{L_{\alpha_h}}$)}")
    doc.append(r"Se determina mediante correcciones tridimensionales (Alargamiento) de la cola horizontal:")
    doc.append(r"\[")
    doc.append(f"  C_{{L_{{\\alpha_h}}}} = \\boxed{{{results.get('CL_alpha_h', 0):.4f}}} \\text{{ rad}}^{{-1}}")
    doc.append(r"\]")

    # de_da
    doc.append(r"\subsection{Gradiente de Deflexión de la Estela ($d\epsilon/d\alpha$)}")
    doc.append(r"\begin{equation}")
    doc.append(r"  \frac{d\epsilon}{d\alpha} = \frac{2 C_{L_\alpha}}{\pi e AR}")
    doc.append(r"\end{equation}")
    doc.append(r"Sustituyendo (empleando factores de aproximación):")
    doc.append(r"\[")
    doc.append(f"  \\frac{{d\\epsilon}}{{d\\alpha}} = \\boxed{{{results.get('de_da', 0):.4f}}}")
    doc.append(r"\]")

    # Cm_alpha
    doc.append(r"\subsection{Derivada de Estabilidad Estática Longitudinal ($C_{m_\alpha}$)}")
    doc.append(r"\begin{equation}")
    doc.append(r"  C_{m_\alpha} = C_{L_\alpha} (x_{cg} - x_{ac}) - C_{L_{\alpha_h}} \eta_h V_H \left(1 - \frac{d\epsilon}{d\alpha}\right)")
    doc.append(r"\end{equation}")
    doc.append(r"Sustituyendo valores:")
    doc.append(r"\[")
    doc.append(f"  C_{{m_\\alpha}} = {results.get('CL_alpha', 0):.4f} ({results.get('x_cg', 0):.4f} - {results.get('x_ac', 0):.4f}) - ({results.get('CL_alpha_h', 0):.4f})({results.get('eta_h', 0):.2f})({results.get('V_H', 0):.4f})\\left(1 - {results.get('de_da', 0):.4f}\\right) = \\boxed{{{results.get('Cm_alpha', 0):.4f}}} \\text{{ rad}}^{{-1}}")
    doc.append(r"\]")

    # Neutral point
    doc.append(r"\subsection{Punto Neutro ($x_{NP}$)}")
    doc.append(r"\begin{equation}")
    doc.append(r"  x_{NP} = x_{ac} + \frac{C_{L_{\alpha_h}} \eta_h V_H \left(1 - \frac{d\epsilon}{d\alpha}\right)}{C_{L_\alpha}}")
    doc.append(r"\end{equation}")
    doc.append(r"Sustituyendo valores:")
    doc.append(r"\[")
    doc.append(f"  x_{{NP}} = {results.get('x_ac', 0):.4f} + \\frac{{({results.get('CL_alpha_h', 0):.4f})({results.get('eta_h', 0):.2f})({results.get('V_H', 0):.4f})\\left(1 - {results.get('de_da', 0):.4f}\\right)}}{{{results.get('CL_alpha', 0):.4f}}} = \\boxed{{{results.get('x_NP', 0):.4f}}}")
    doc.append(r"\]")

    # Static margin
    doc.append(r"\subsection{Margen Estático ($SM$)}")
    doc.append(r"\begin{equation}")
    doc.append(r"  SM = x_{NP} - x_{cg}")
    doc.append(r"\end{equation}")
    doc.append(r"Sustituyendo valores:")
    doc.append(r"\[")
    doc.append(f"  SM = {results.get('x_NP', 0):.4f} - {results.get('x_cg', 0):.4f} = \\boxed{{{results.get('static_margin', 0):.4f}}}")
    doc.append(r"\]")

    # Cm_0
    doc.append(r"\subsection{Momento de Cabeceo a Sustentación Nula ($C_{m_0}$)}")
    doc.append(r"Derivado de la configuración y perfil aerodinámico de la aeronave:")
    doc.append(r"\[")
    doc.append(f"  C_{{m_0}} = \\boxed{{{results.get('Cm_0', 0):.4f}}}")
    doc.append(r"\]")

    # Cm_de
    doc.append(r"\subsection{Efectividad del Elevador ($C_{m_{\delta e}}$)}")
    doc.append(r"\begin{equation}")
    doc.append(r"  C_{m_{\delta e}} = - \eta_h V_H \tau_e C_{L_{\alpha_h}}")
    doc.append(r"\end{equation}")
    doc.append(r"Sustituyendo valores:")
    doc.append(r"\[")
    doc.append(f"  C_{{m_{{\\delta e}}}} = - ({results.get('eta_h', 0):.2f})({results.get('V_H', 0):.4f})({results.get('tau_e', 0):.4f})({results.get('CL_alpha_h', 0):.4f}) = \\boxed{{{results.get('Cm_de', 0):.4f}}} \\text{{ rad}}^{{-1}}")
    doc.append(r"\]")

    # alpha trim
    doc.append(r"\subsection{Ángulo de Ataque de Trim ($\alpha_{trim}$)}")
    doc.append(r"\begin{equation}")
    doc.append(r"  \alpha_{trim} = -\frac{C_{m_0}}{C_{m_\alpha}} \times \frac{180}{\pi}")
    doc.append(r"\end{equation}")
    doc.append(r"Sustituyendo valores:")
    doc.append(r"\[")
    doc.append(f"  \\alpha_{{trim}} = -\\frac{{{results.get('Cm_0', 0):.4f}}}{{{results.get('Cm_alpha', 0):.4f}}} \\times \\frac{{180}}{{\\pi}} = \\boxed{{{results.get('alpha_trim_deg', 0):.4f}^\\circ}}")
    doc.append(r"\]")


    # --- Sección 3: Estabilidad Direccional (Estática) ---
    doc.append(r"\section{Estabilidad Direccional y Lateral (Estática)}")

    # V_V
    doc.append(r"\subsection{Coeficiente de Volumen de Cola Vertical ($V_V$)}")
    doc.append(r"\begin{equation}")
    doc.append(r"  V_V = \frac{S_v \cdot l_v}{S_w \cdot b}")
    doc.append(r"\end{equation}")
    doc.append(r"Sustituyendo valores:")
    doc.append(r"\[")
    doc.append(f"  V_V = \\frac{{{results.get('S_v', 0):.2f} \\times {results.get('l_v', 0):.2f}}}{{{results.get('S_w', 0):.2f} \\times {results.get('b', 0):.2f}}} = \\boxed{{{results.get('V_V', 0):.4f}}}")
    doc.append(r"\]")

    # CL_alpha_v
    doc.append(r"\subsection{Gradiente de Sustentación de la Cola Vertical ($C_{L_{\alpha_v}}$)}")
    doc.append(r"Calculado en base a su geometría:")
    doc.append(r"\[")
    doc.append(f"  C_{{L_{{\\alpha_v}}}} = \\boxed{{{results.get('CL_alpha_v', 0):.4f}}} \\text{{ rad}}^{{-1}}")
    doc.append(r"\]")

    # Cn_beta
    doc.append(r"\subsection{Estabilidad Direccional Estática / Efecto Veleta ($C_{n_\beta}$)}")
    doc.append(r"\begin{equation}")
    doc.append(r"  C_{n_\beta} = C_{n_{\beta_{fus}}} + V_V \eta_v C_{L_{\alpha_v}}")
    doc.append(r"\end{equation}")
    doc.append(r"Asumiendo aporte de los componentes y sustituyendo:")
    doc.append(r"\[")
    doc.append(f"  C_{{n_\\beta}} = \\text{{Aportes}} + ({results.get('V_V', 0):.4f})({results.get('eta_v', 0):.2f})({results.get('CL_alpha_v', 0):.4f}) = \\boxed{{{results.get('Cn_beta', 0):.4f}}} \\text{{ rad}}^{{-1}}")
    doc.append(r"\]")

    # Cl_beta
    doc.append(r"\subsection{Efecto Diedro ($C_{l_\beta}$)}")
    doc.append(r"\begin{equation}")
    doc.append(r"  C_{l_\beta} \approx -\frac{C_{L_\alpha} \Gamma}{4} + \text{Aportes Cola/Fuselaje}")
    doc.append(r"\end{equation}")
    doc.append(r"Evaluando la configuración:")
    doc.append(r"\[")
    doc.append(f"  C_{{l_\\beta}} = \\boxed{{{results.get('Cl_beta', 0):.4f}}} \\text{{ rad}}^{{-1}}")
    doc.append(r"\]")

    # Cn_dr
    doc.append(r"\subsection{Efectividad del Timón de Dirección ($C_{n_{\delta r}}$)}")
    doc.append(r"\begin{equation}")
    doc.append(r"  C_{n_{\delta r}} = - V_V \eta_v \tau_r C_{L_{\alpha_v}}")
    doc.append(r"\end{equation}")
    doc.append(r"Sustituyendo:")
    doc.append(r"\[")
    doc.append(f"  C_{{n_{{\\delta r}}}} = - ({results.get('V_V', 0):.4f})({results.get('eta_v', 0):.2f})({results.get('tau_r', 0):.4f})({results.get('CL_alpha_v', 0):.4f}) = \\boxed{{{results.get('Cn_dr', 0):.4f}}} \\text{{ rad}}^{{-1}}")
    doc.append(r"\]")

    # Cl_da
    doc.append(r"\subsection{Efectividad de Alerones ($C_{l_{\delta a}}$)}")
    doc.append(r"Determinada a partir de la geometría y efectividad del alerón en el ala:")
    doc.append(r"\[")
    doc.append(f"  C_{{l_{{\\delta a}}}} = \\boxed{{{results.get('Cl_da', 0):.4f}}} \\text{{ rad}}^{{-1}}")
    doc.append(r"\]")


    # --- Sección 4: Estabilidad Dinámica Longitudinal ---
    doc.append(r"\section{Estabilidad Dinámica Longitudinal}")
    doc.append(r"\subsection{Matriz de Estado (A)}")
    doc.append(r"La respuesta dinámica se evalúa mediante los autovalores de la matriz de estado longitudinal $A_{lon}$:")
    doc.append(r"\[")
    doc.append(r"  A_{lon} = " + format_matrix(results.get('A_lon', [])))
    doc.append(r"\]")

    doc.append(r"\subsection{Autovalores}")
    doc.append(r"\begin{itemize}")
    for eig in results.get('eig_lon', []):
        doc.append(f"  \\item $\\lambda = {format_complex(eig)}$")
    doc.append(r"\end{itemize}")

    doc.append(r"\subsection{Modos Dinámicos}")
    doc.append(r"\begin{table}[H]")
    doc.append(r"\centering")
    doc.append(r"\begin{tabular}{lccc}")
    doc.append(r"\toprule")
    doc.append(r"\textbf{Modo} & \textbf{$\omega_n$ [rad/s]} & \textbf{$\zeta$} & \textbf{Periodo $T$ [s]} \\")
    doc.append(r"\midrule")
    doc.append(f"Phugoide & {results.get('phugoid_wn', 0):.4f} & {results.get('phugoid_zeta', 0):.4f} & {results.get('phugoid_period', 0):.2f} \\\\")
    doc.append(f"Corto Periodo & {results.get('short_period_wn', 0):.4f} & {results.get('short_period_zeta', 0):.4f} & {results.get('short_period_period', 0):.2f} \\\\")
    doc.append(r"\bottomrule")
    doc.append(r"\end{tabular}")
    doc.append(r"\end{table}")
    doc.append(r"El \textbf{Modo Phugoide} exhibe oscilaciones lentas que intercambian altitud y velocidad, mientras que el \textbf{Corto Periodo} amortigua rápidamente las perturbaciones en el ángulo de ataque.")


    # --- Sección 5: Estabilidad Dinámica Latero-Direccional ---
    doc.append(r"\section{Estabilidad Dinámica Latero-Direccional}")
    doc.append(r"\subsection{Matriz de Estado (A)}")
    doc.append(r"Evolución de las variables laterales expresada a través de la matriz $A_{lat}$:")
    doc.append(r"\[")
    doc.append(r"  A_{lat} = " + format_matrix(results.get('A_lat', [])))
    doc.append(r"\]")

    doc.append(r"\subsection{Autovalores}")
    doc.append(r"\begin{itemize}")
    for eig in results.get('eig_lat', []):
        doc.append(f"  \\item $\\lambda = {format_complex(eig)}$")
    doc.append(r"\end{itemize}")

    doc.append(r"\subsection{Modos Dinámicos}")
    doc.append(r"\begin{table}[H]")
    doc.append(r"\centering")
    doc.append(r"\begin{tabular}{lccc}")
    doc.append(r"\toprule")
    doc.append(r"\textbf{Modo} & \textbf{$\omega_n$ [rad/s] o $\tau$ [s]} & \textbf{$\zeta$} & \textbf{Periodo $T$ [s]} \\")
    doc.append(r"\midrule")
    doc.append(f"Rolandés (Dutch Roll) & {results.get('dutch_roll_wn', 0):.4f} & {results.get('dutch_roll_zeta', 0):.4f} & {results.get('dutch_roll_period', 0):.2f} \\\\")
    doc.append(f"Convergencia de Rolido & $\\tau = {results.get('roll_tau', 0):.4f}$ & - & - \\\\")
    doc.append(f"Espiral & $\\tau = {results.get('spiral_tau', 0):.4f}$ & - & - \\\\")
    doc.append(r"\bottomrule")
    doc.append(r"\end{tabular}")
    doc.append(r"\end{table}")
    doc.append(r"El modo \textbf{Rolandés} es un movimiento acoplado oscilatorio de guiñada y alabeo. El modo de \textbf{Rolido} dicta la rapidez de convergencia en la tasa de alabeo, y el modo \textbf{Espiral} indica la tendencia a entrar en un viraje lento divergente o volver gradualmente a nivel.")


    # --- Sección 6: Resumen y Criterios ---
    cm_alpha_ok = results.get('Cm_alpha', 0) < 0
    cn_beta_ok = results.get('Cn_beta', 0) > 0
    cl_beta_ok = results.get('Cl_beta', 0) < 0
    sm_ok = 0.05 <= results.get('static_margin', 0) <= 0.15

    # Check stability of modes (all roots must have negative real part)
    all_eigs = results.get('eig_lon', []) + results.get('eig_lat', [])
    modes_stable = all((e.real < 0 if isinstance(e, complex) else float(e) < 0) for e in all_eigs) if all_eigs else False
    
    sp_damping_ok = results.get('short_period_zeta', 0) >= 0.3
    dr_damping_ok = results.get('dutch_roll_zeta', 0) >= 0.04

    doc.append(r"\section{Resumen y Criterios de Evaluación}")
    doc.append(r"\begin{table}[H]")
    doc.append(r"\centering")
    doc.append(r"\begin{tabular}{llc}")
    doc.append(r"\toprule")
    doc.append(r"\textbf{Criterio} & \textbf{Condición de Diseño} & \textbf{Estado} \\")
    doc.append(r"\midrule")
    doc.append(rf"$C_{{m_\alpha}} < 0$ & Estabilidad Estática Longitudinal & {get_status(cm_alpha_ok)} \\\\")
    doc.append(rf"$C_{{n_\beta}} > 0$ & Estabilidad Estática Direccional & {get_status(cn_beta_ok)} \\\\")
    doc.append(rf"$C_{{l_\beta}} < 0$ & Efecto Diedro Positivo & {get_status(cl_beta_ok)} \\\\")
    doc.append(rf"Margen Estático & Entre 5\% y 15\% MAC & {get_status(sm_ok)} \\\\")
    doc.append(rf"Modos Dinámicos & Todos estables ($Re(\lambda) < 0$) & {get_status(modes_stable)} \\\\")
    doc.append(rf"Amortiguamiento CP & $\zeta \ge 0.3$ & {get_status(sp_damping_ok)} \\\\")
    doc.append(rf"Amortiguamiento Rolandés & $\zeta \ge 0.04$ & {get_status(dr_damping_ok)} \\\\")
    doc.append(r"\bottomrule")
    doc.append(r"\end{tabular}")
    doc.append(r"\end{table}")


    # --- Sección 7: Conclusiones ---
    all_passed = all([cm_alpha_ok, cn_beta_ok, cl_beta_ok, sm_ok, modes_stable, sp_damping_ok, dr_damping_ok])

    doc.append(r"\section{Conclusiones}")
    if all_passed:
        doc.append(r"El diseño del HALE UAV \textbf{cumple con todos los criterios de estabilidad estática y dinámica}. Los márgenes de estabilidad son adecuados y los modos dinámicos se encuentran apropiadamente amortiguados para las fases de vuelo nominales. Las superficies de control dimensionadas y la posición del centro de gravedad aseguran un desempeño aerodinámico predecible y seguro.")
    else:
        doc.append(r"El diseño del HALE UAV \textbf{no cumple} con todos los criterios de estabilidad. Se recomienda realizar una revisión del dimensionamiento iterativo basándose en los siguientes puntos críticos:")
        doc.append(r"\begin{itemize}")
        if not cm_alpha_ok: doc.append(r"\item Incrementar el área de la cola horizontal ($S_h$) o adelantar el centro de gravedad para asegurar $C_{m_\alpha} < 0$.")
        if not cn_beta_ok: doc.append(r"\item Incrementar el área ($S_v$) o el brazo de palanca ($l_v$) de la cola vertical para mejorar el efecto veleta ($C_{n_\beta}$).")
        if not cl_beta_ok: doc.append(r"\item Ajustar el ángulo de diedro ($\Gamma$) del ala principal para garantizar un momento de restauración $C_{l_\beta} < 0$.")
        if not sm_ok: doc.append(r"\item Reposicionar el centro de gravedad ($x_{cg}$) o ajustar la geometría para obtener un Margen Estático operativo entre 5\% y 15\%.")
        if not modes_stable: doc.append(r"\item Existen modos dinámicos inestables ($Re(\lambda) \ge 0$) que requerirán un rediseño de las superficies de estabilización o la implementación de un sistema de control activo avanzado.")
        if not sp_damping_ok: doc.append(r"\item El modo de corto periodo carece del amortiguamiento necesario; se sugiere aumentar el volumen de la cola horizontal ($V_H$).")
        if not dr_damping_ok: doc.append(r"\item El modo rolandés carece del amortiguamiento mínimo requerido; se recomienda evaluar un incremento en el área del estabilizador vertical.")
        doc.append(r"\end{itemize}")

    doc.append(r"\end{document}")
    
    tex_content = "\n".join(doc)
    
    # Save the .tex file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(tex_content)
        
    print(f"Reporte LaTeX guardado en: {filepath}")
    
    # Intentar compilar a PDF automáticamente
    import subprocess
    import os
    
    # Ruta del compilador pdflatex de MiKTeX basada en la instalación del usuario
    pdflatex_path = r"C:\Users\emili\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe"
    
    if os.path.exists(pdflatex_path):
        try:
            print("Compilando a PDF con MiKTeX...")
            # Extraer directorio y nombre del archivo
            work_dir = os.path.dirname(filepath)
            filename = os.path.basename(filepath)
            
            # Ejecutar pdflatex
            process = subprocess.run(
                [pdflatex_path, "-interaction=nonstopmode", filename],
                cwd=work_dir,
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                print("¡Compilación PDF exitosa!")
            else:
                print("Advertencia: La compilación PDF tuvo errores o requerimientos faltantes.")
                print(process.stdout)
        except Exception as e:
            print(f"Error al compilar PDF: {e}")
    else:
        print(f"Nota: No se encontró pdflatex en {pdflatex_path}. El archivo .tex está listo para compilarse manualmente.")
