# globals.py
# Constantes físicas y de diseño del HALE UAV proporcionadas por el usuario.
# Estos valores están "hardcoded" como se solicitó y no son modificables desde la UI.

class UAVConstants:
    # --- Parámetros de Diseño (Sizing) ---
    WEIGHT_N = 490.5          # Peso en Newtons (W)
    MASS_KG = 50.0            # Masa en kg
    
    SURFACE_AREA = 14.7       # Superficie Alar S [m^2]
    ASPECT_RATIO = 18.0       # Alargamiento (AR)
    WINGSPAN = 16.26653       # Envergadura (b) [m]
    SEMI_WINGSPAN = 8.133265  # Semienvergadura (b/2) [m]
    WING_LOADING = 3.396392   # Carga Alar (CA) [kg/m^2]
    MAC = 0.905018            # Cuerda Aerodinámica Media (CAM o c = S/b) [m]
    
    # --- Parámetros Operativos Máximos / Referencia ---
    MAX_ALTITUDE_M = 25000.0  # Techo máximo estratosférico [m]
    
    # Datos de referencia a 25km (estos luego vendrán de la tabla de atmósfera también)
    RHO_25KM = 0.04008        # Densidad a 25km [kg/m^3]
    VELOCITY_REF = 39.0       # Velocidad de referencia [m/s]
    CL_REF = 1.0931           # Coeficiente de sustentación de referencia
    
    # --- Latitudes de México (para futuros cálculos solares) ---
    LAT_MEXICO_NORTH = 32.71  # Tijuana / Mexicali approx (Latitud Norte)
    LAT_MEXICO_CENTER = 23.63 # Trópico de Cáncer / Centro de México
    LAT_MEXICO_SOUTH = 14.53  # Frontera sur (Chiapas)

    # --- Empenaje Horizontal ---
    S_HTAIL = 2.0             # Área estabilizador horizontal [m²]
    SPAN_HTAIL = 3.5          # Envergadura estabilizador horizontal [m]
    L_HTAIL = 6.2             # Distancia CG → CA del estabilizador horizontal [m]
    ELEVATOR_CHORD_RATIO = 0.25  # Relación cuerda elevador / cuerda cola
    ELEVATOR_SPAN_RATIO = 0.90   # Relación envergadura elevador / envergadura cola
    ELEVATOR_MAX_DEF_DEG = 25.0  # Deflexión máxima elevador [deg]

    # --- Empenaje Vertical ---
    S_VTAIL = 1.0             # Área estabilizador vertical [m²]
    SPAN_VTAIL = 1.5          # Envergadura (altura) estabilizador vertical [m]
    L_VTAIL = 6.0             # Distancia CG → CA del estabilizador vertical [m]
    RUDDER_CHORD_RATIO = 0.30    # Relación cuerda timón / cuerda cola vertical
    RUDDER_SPAN_RATIO = 1.00     # Relación envergadura timón / envergadura cola vertical
    RUDDER_MAX_DEF_DEG = 30.0    # Deflexión máxima timón [deg]

    # --- Posiciones CG y Centro Aerodinámico ---
    CG_POSITION_MAC = 0.25    # Posición del CG como fracción de MAC (25% MAC)
    AC_POSITION_MAC = 0.25    # Centro aerodinámico del ala como fracción de MAC
    DIHEDRAL_DEG = 5.0        # Ángulo de diedro del ala [deg]

    # --- Eficiencias de Cola ---
    ETA_H = 0.90              # Eficiencia del estabilizador horizontal (por estela)
    ETA_V = 0.90              # Eficiencia del estabilizador vertical
    TAU_ELEVATOR = 0.50       # Efectividad del elevador (τ_e)
    TAU_RUDDER = 0.50         # Efectividad del timón (τ_r)

    # --- Alerones ---
    AILERON_Y_INNER = 0.65    # Posición interna del alerón (fracción de semienvergadura)
    AILERON_Y_OUTER = 0.95    # Posición externa del alerón (fracción de semienvergadura)
    AILERON_CHORD_RATIO = 0.22  # Relación cuerda alerón / cuerda ala
    TAU_AILERON = 0.40        # Efectividad del alerón (τ_a)
