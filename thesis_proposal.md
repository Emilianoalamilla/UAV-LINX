# Proyecto LINX: Diseño Conceptual de UAV Solar de Gran Altitud y Larga Autonomía (HALE)

**Autores:** Josua Emiliano Alamilla Jimenez, Roció Nayeli Oliva González
**Asesor:** Dr. Gustavo Medina Tanco

---

## 1. Alcance del Proyecto (Scope)

El objetivo principal del proyecto LINX es diseñar, desarrollar y validar un Vehículo Aéreo No Tripulado (UAV) propulsado por energía solar, capaz de transportar y mantener operativa una carga útil de hasta 5 kg a gran altitud (estratosfera) durante periodos prolongados (varios meses), de forma autónoma, segura y energéticamente autosuficiente.

- **Autonomía:** Totalmente autónomo con capacidad de navegación, estabilización y gestión de energía.
- **Área de Operación:** Cercano a la latitud de México, entre 19° y 24° N.
- **Requerimientos de Diseño Clave:**
  - Peso máximo de despegue (MTOW): 30 kg
  - Envergadura: 13.384 m
  - Superficie alar: 14.928 m²
- **Marco Legal:** Regulado bajo la NOM-107-SCT3-2019, con permisos obligatorios de la AFAC para operaciones BVLOS (Beyond Visual Line of Sight) y autorización para Aeronave Experimental para vuelos por encima de los 122 m (400 ft).

## 2. Metodología y Dimensionamiento

El proyecto está estructurado en cinco fases principales, dividiendo el presupuesto y esfuerzo:
- **Fase A:** Culminada.
- **Fase B (Diseño Conceptual - 38%):** Estimación de pesos, selección de configuración, dimensionamiento inicial y requerimientos.
- **Fase C (Diseño Detallado - 19%):** Análisis aerodinámico profundo (método de paneles, CFD), diseño estructural y análisis de estabilidad.
- **Fase D (Manufactura y Pruebas - 38%):** Producción de prototipos y modelos de ingeniería, pruebas de estrés y vuelo.
- **Fase E (Documentación y Entrega - 6%):** Manuales y reporte final de tesis.

### Ecuaciones de Dimensionamiento y Rendimiento
Partiendo de la información estructurada, el diseño inicial estima el peso total de despegue ($W_{TO}$) como la suma de sus componentes:
$$ W_{TO} = W_{PL} + W_{S} + W_{B} + W_{E} $$
Donde $W_{PL}$ es el peso de carga útil, $W_S$ es el peso de sistemas, $W_B$ es el peso de baterías y $W_E$ es el peso vacío.

Para el análisis aerodinámico y el equilibrio en vuelo, la fuerza de sustentación ($L$) se iguala al peso:
$$ L = W = \frac{1}{2} \rho v^2 S C_L $$

El cálculo de la potencia requerida y disponible es fundamental. La potencia en el eje (Brake Horse Power, BHP) para el motor eléctrico se estima como:
$$ BHP = \frac{V \cdot I \cdot \eta_{motor}}{746} $$

El empuje ($T$) proporcionado por las hélices y la eficiencia propulsiva ($\eta_P$) se calculan mediante:
$$ T = C_T \rho n^2 D^4 $$
$$ \eta_P = \frac{T \cdot V}{BHP} $$

Además, el balance energético (Power Budget) toma en consideración las eficiencias de la cadena de potencia ($\eta_{cadena} = \eta_{prop} \cdot \eta_{motor} \cdot \eta_{ESC}$).

## 3. Toma de Decisiones y Análisis de Riesgos

### Descomposición Funcional y QFD
El proceso de diseño partió de un **Análisis de Descomposición Funcional** para mapear la función global hacia los subsistemas específicos (fuselaje, propulsión, potencia, etc.). Posteriormente, se tradujeron estos requerimientos técnicos utilizando **QFD** y se evaluaron usando el **Proceso de Jerarquía Analítica (AHP de Saaty)** para darles peso y prioridad.
- **Aerodinámica:** Se ponderó como prioritario generar sustentación suficiente en crucero (R04: 0.0704) y reducir arrastre parásito para maximizar L/D (R05: 0.0704).
- **Manufacturabilidad:** Se priorizó el limitar las deformaciones (R19: 0.0405) y validar la estructura ante vibraciones y cargas (R22: 0.0386).

### Análisis de Modos de Falla y Efectos (FMEA)
Para garantizar la seguridad y fiabilidad del UAV en misiones BVLOS estratosféricas, se utilizó la matriz **FMEA** multiplicando Probabilidad, Severidad y Detección para obtener el Número de Prioridad de Riesgo (RPN). 
Los riesgos más probables y críticos identificados fueron:
1. **Déficit energético (noche) [RPN: 15]:** Ocurrente en crucero.
2. **Fallo de Motor/ESC [RPN: 12]:** Crítico durante el ascenso.
3. **Pérdida de Enlace C2 [RPN: 12]:** Crítico en crucero a gran altitud.
4. **Hard Landing [RPN: 12]:** Durante la aproximación final.

## 4. Trabajo Realizado e Integración

Se han alcanzado importantes hitos en el diseño:
- **Configuración Aerodinámica:** Se seleccionó un modelo de **fuselaje integrado** con estabilizadores y motores en configuración "Tandem Pusher". Se analizó el efecto del ángulo diedro y alabeo para optimizar la captación de luz solar a lo largo del día.
- **Sistema Propulsivo:** 
  - Se requiere un empuje capaz de mantener el vuelo en condiciones estratosféricas (baja densidad, $v \approx 39$ m/s). 
  - Dos motores seleccionados con hélices de 1.35 m de diámetro a 50 rev/s (aprox 6720 W por motor).
- **Sistema de Potencia Solar:** 
  - Se limitó el peso de los paneles a 5 kg. 
  - Se realizó un benchmarking de diversas celdas solares, seleccionando celdas Spectrolab de alta eficiencia (GaAs) debido a que ofrecen el mejor margen de diseño eléctrico (voltaje y corriente). 
  - El perfil de insolación fue simulado para el solsticio de invierno (noche más larga) a la latitud de la CDMX (19.4°).
- **Herramientas Utilizadas:** CAD para los renders, XFLR5/CFD para perfiles alares (NACA 0012, SG6043).
- **Estado del Arte (Literatura):** Integración de libros clave como "Aircraft Design: A Systems Engineering Approach", "Raymer", metodologías de diseño de hélices de la NASA, artículos de estabilidad, etc.

## 4. Secciones de Trabajo del Equipo

- **Administración:** Gestión del proyecto, costos (Total estimado: ~$1,131,165 MXN), y cumplimiento de la NOM.
- **Estructuras:** Diseño y manufactura de componentes mecánico-estructurales (uso de Epoxy, FOAM, piezas impresas 3D en ASA/ABS), validación de cargas y rigidez.
- **Electrónica:** Sistemas de potencia solar (MPPT), baterías (INR, Li-Ion, BMS), control de vuelo y comunicaciones.
- **Logística:** Permisos, patentes y viajes de prueba.

---
_Documento generado para visualización en repositorios Git y LaTeX._
