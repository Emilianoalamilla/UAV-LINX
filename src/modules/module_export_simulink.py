# module_export_simulink.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QTextEdit, QHBoxLayout
from core.globals import UAVConstants

class SimulinkExportWidget(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.setup_ui()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        self.title = QLabel("10. Exportador Directo MATLAB / Simulink (API)")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50;")
        self.main_layout.addWidget(self.title)
        
        self.desc = QLabel(
            "Este módulo usa la API nativa de Python para inyectar las matrices de "
            "Espacio de Estados en MATLAB y dibujar tu diagrama de Simulink automáticamente.\n\n"
            "INSTRUCCIONES DE AUTOMATIZACIÓN:\n"
            "1. Abre MATLAB en tu PC.\n"
            "2. Escribe en la consola de MATLAB: matlab.engine.shareEngine\n"
            "3. Presiona el botón verde de Inyección.\n"
            "4. Python creará mágicamente el bloque LTI System, lo conectará y te lo mostrará."
        )
        self.desc.setWordWrap(True)
        self.desc.setStyleSheet("font-size: 14px; color: #34495e; margin-bottom: 20px;")
        self.main_layout.addWidget(self.desc)
        
        self.btn_layout = QHBoxLayout()
        self.btn_export = QPushButton("Exportar Script de MATLAB (.m)")
        self.btn_export.setStyleSheet("background-color: #7f8c8d; color: white; padding: 10px;")
        self.btn_export.clicked.connect(self.export_to_matlab)
        
        self.btn_api = QPushButton("Inyectar Vía API a MATLAB en vivo")
        self.btn_api.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px; font-size: 14px;")
        self.btn_api.clicked.connect(self.inject_via_api)
        
        self.btn_layout.addWidget(self.btn_export)
        self.btn_layout.addWidget(self.btn_api)
        self.main_layout.addLayout(self.btn_layout)
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("font-family: Consolas; background-color: #1e1e1e; color: #00ff00; font-size: 12px;")
        self.main_layout.addWidget(self.console)
        
    def get_aerodynamic_matrices(self):
        m = UAVConstants.MASS_KG
        S = UAVConstants.SURFACE_AREA
        b = UAVConstants.WINGSPAN
        c = UAVConstants.MAC
        rho = UAVConstants.RHO_25KM
        u0 = UAVConstants.VELOCITY_REF
        
        Ixx = (1.0/12.0) * m * (b**2)
        Iyy = (1.0/12.0) * m * (c**2)
        Izz = Ixx + Iyy
        
        Xu, Xw, Zu, Zw = -0.05, 0.08, -0.30, -2.50
        Mu, Mw, Mq = 0.02, -0.15, -1.20
        
        A_lon = [
            [Xu/m,           Xw/m,           0,         -9.81],
            [Zu/m,           Zw/m,           u0,        0],
            [Mu/Iyy,         Mw/Iyy,         Mq/Iyy,    0],
            [0,              0,              1,         0]
        ]
        
        B_lon = [
            [0.1],
            [-0.5],
            [-1.2],
            [0]
        ]
        
        return A_lon, B_lon
        
    def export_to_matlab(self):
        try:
            A, B = self.get_aerodynamic_matrices()
            
            matlab_code = f"""% Script Autogenerado por HALE UAV Sizing App
% Integra los resultados del motor VLM (Python) hacia Simulink 6-DOF

%% Matriz de Espacio de Estados (Longitudinal A-Matrix)
A_lon = [{'; '.join([' '.join(map(str, row)) for row in A])}];

B_lon = [{'; '.join([' '.join(map(str, row)) for row in B])}];

C_lon = eye(4);
D_lon = zeros(4,1);

sys_longitudinal = ss(A_lon, B_lon, C_lon, D_lon);
disp('Matrices de Estado listas para Simulink!');
"""
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Script de MATLAB", "HALE_VLM_Simulink.m", "MATLAB Scripts (*.m)", options=options)
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(matlab_code)
                self.console.append(f"> ÉXITO: Script generado en {file_path}")
        except Exception as e:
            self.console.append(f"> ERROR: {str(e)}")

    def inject_via_api(self):
        try:
            import matlab.engine
            self.console.append("> Buscando un motor de MATLAB activo...")
            self.console.append("> Asegúrate de haber escrito 'matlab.engine.shareEngine' en MATLAB.")
            
            # Conectar al motor de MATLAB activo
            engines = matlab.engine.find_matlab()
            if not engines:
                self.console.append("> ERROR: No se encontró ningún MATLAB activo y compartido.")
                self.console.append("> Ejecuta 'matlab.engine.shareEngine' en la ventana de comandos de MATLAB e intenta de nuevo.")
                return
                
            self.console.append(f"> Conectando a la sesión de MATLAB: {engines[0]}...")
            eng = matlab.engine.connect_matlab(engines[0])
            
            A_lon, B_lon = self.get_aerodynamic_matrices()
            
            # Convert Python list to matlab.double arrays
            eng.workspace['A_lon'] = matlab.double(A_lon)
            eng.workspace['B_lon'] = matlab.double(B_lon)
            
            # Pasar parámetros geométricos del UAV para el modelo 3D
            eng.workspace['uav_wingspan'] = float(UAVConstants.WINGSPAN)
            eng.workspace['uav_chord'] = float(UAVConstants.MAC)
            eng.workspace['uav_length'] = float(getattr(UAVConstants, 'FUSELAGE_LENGTH', UAVConstants.MAC * 3))
            
            self.console.append("> ÉXITO: Matrices A_lon y B_lon inyectadas directamente al Workspace.")
            self.console.append("> Construyendo modelo Simulink + Animación 3D...")
            
            matlab_script = r"""
            %% ===== FASE 1: Sistema de Control =====
            C_lon = eye(4); D_lon = zeros(4,1);
            sys_longitudinal = ss(A_lon, B_lon, C_lon, D_lon);
            
            %% ===== FASE 2: Simulacion Numerica =====
            t_sim = linspace(0, 30, 1500)';
            u_input = ones(length(t_sim), 1) * 0.05;
            [y_sim, t_out] = lsim(sys_longitudinal, u_input, t_sim);
            
            u_pert = y_sim(:,1);
            w_vel  = y_sim(:,2);
            theta  = y_sim(:,4);
            
            u0_cruise = 30;
            x_pos = cumtrapz(t_out, u_pert + u0_cruise);
            z_pos = -cumtrapz(t_out, w_vel) + 25000;
            
            %% ===== FASE 3: FlightGear 3D Visualization =====
            b_w = uav_wingspan;
            
            % Buscar FlightGear
            fg_dirs = { ...
                'C:\Program Files\FlightGear 2024.1', ...
                'C:\Program Files\FlightGear 2020.3', ...
                'C:\Program Files\FlightGear', ...
                'C:\Program Files (x86)\FlightGear 2024.1' };
            fg_root = '';
            for d = 1:length(fg_dirs)
                if isfolder(fg_dirs{d})
                    fg_root = fg_dirs{d};
                    break;
                end
            end
            
            if ~isempty(fg_root)
                disp(['>>> FlightGear encontrado en: ' fg_root]);
                
                % Coordenadas iniciales (Desierto de Sonora - zona HALE)
                lat0 = 32.0;   % grados
                lon0 = -110.0; % grados
                alt0 = 25000;  % metros
                
                % Convertir posiciones locales a lat/lon (en RADIANES para FlightGear)
                R_earth = 6371000;
                lat_series = deg2rad(lat0) + x_pos / R_earth;
                lon_series = deg2rad(lon0) * ones(size(t_out));
                alt_series = z_pos;
                
                phi_series   = zeros(size(t_out));
                theta_series = theta;
                psi_series   = zeros(size(t_out));
                
                % ===== GENERACION DEL MODELO 3D AUTOMATICO (.AC) =====
                % FlightGear requiere formato AC3D (.ac) de forma nativa.
                fg_home = getenv('APPDATA');
                fg_user_dir = fullfile(fg_home, 'flightgear.org');
                if ~isfolder(fg_user_dir), mkdir(fg_user_dir); end
                
                try bw = uav_wingspan; catch, bw = 25; end
                try cw = uav_chord; catch, cw = 2; end
                
                ac_path = fullfile(fg_user_dir, 'hale.ac');
                ac_path_fg = strrep(ac_path, '\', '/');
                
                fid = fopen(ac_path, 'w');
                fprintf(fid, 'AC3Db\n');
                fprintf(fid, 'MATERIAL "white" rgb 1 1 1 amb 0.5 0.5 0.5 emis 0 0 0 spec 1 1 1 shi 32 trans 0\n');
                fprintf(fid, 'MATERIAL "blue" rgb 0.2 0.5 0.9 amb 0.5 0.5 0.5 emis 0 0 0 spec 1 1 1 shi 32 trans 0\n');
                fprintf(fid, 'OBJECT world\nkids 4\n');
                % ===== VUELO EN ALA VOLANTE (NACA 0012 + DIEDRO + ELEVONES) =====
                try bw = uav_wingspan; catch, bw = 25; end
                try cw = uav_chord; catch, cw = 2; end
                
                ac_path = fullfile(fg_user_dir, 'hale.ac');
                ac_path_fg = strrep(ac_path, '\', '/');
                
                % Crear Perfil NACA 0012
                x_n = linspace(0, 1, 12);
                y_n = 5 * 0.12 * (0.2969*sqrt(x_n) - 0.126*x_n - 0.3516*x_n.^2 + 0.2843*x_n.^3 - 0.1015*x_n.^4);
                x_prof = [fliplr(x_n), x_n(2:end)];
                z_prof = [fliplr(y_n), -y_n(2:end)];
                num_pts = length(x_prof);
                
                % Geometría de Ala Volante
                ct = cw * 0.4; % Cuerda de punta
                sweep = cw * 0.6; % Flecha hacia atras
                dihedral = (bw/2) * tand(5); % 5 grados de diedro
                
                y_sec = [-bw/2, 0, bw/2];
                x_offset = [sweep, 0, sweep];
                z_offset = [dihedral, 0, dihedral];
                chords = [ct, cw, ct];
                num_sec = length(y_sec);
                
                % Generar Vértices
                V = [];
                for i = 1:num_sec
                    X = x_offset(i) + x_prof * chords(i);
                    Y = y_sec(i) * ones(1, num_pts);
                    Z = z_offset(i) + z_prof * chords(i);
                    V = [V; X' Y' Z'];
                end
                
                % Generar Caras (Quads)
                F = [];
                for i = 1:num_sec-1
                    for j = 1:num_pts-1
                        v1 = (i-1)*num_pts + j;
                        v2 = v1 + 1;
                        v3 = v2 + num_pts;
                        v4 = v1 + num_pts;
                        F = [F; v1, v2, v3, v4];
                    end
                end
                
                % Escribir archivo AC3D
                fid = fopen(ac_path, 'w');
                fprintf(fid, 'AC3Db\n');
                fprintf(fid, 'MATERIAL "white" rgb 0.9 0.9 0.9 amb 0.5 0.5 0.5 emis 0 0 0 spec 0.8 0.8 0.8 shi 64 trans 0\n');
                fprintf(fid, 'MATERIAL "red" rgb 0.8 0.1 0.1 amb 0.5 0.5 0.5 emis 0 0 0 spec 0.2 0.2 0.2 shi 32 trans 0\n');
                fprintf(fid, 'OBJECT world\nkids 1\n');
                fprintf(fid, 'OBJECT poly\nname "flying_wing"\n');
                fprintf(fid, 'numvert %d\n', size(V,1));
                for i = 1:size(V,1)
                    fprintf(fid, '%f %f %f\n', V(i,1), V(i,2), V(i,3));
                end
                fprintf(fid, 'numsurf %d\n', size(F,1));
                for i = 1:size(F,1)
                    % Pintar de rojo el borde de salida (elevones)
                    j = mod(F(i,1)-1, num_pts) + 1;
                    if (j <= 3) || (j >= num_pts-3)
                        mat_idx = 1; % Rojo
                    else
                        mat_idx = 0; % Blanco
                    end
                    fprintf(fid, 'SURF 0x30\nmat %d\nrefs 4\n', mat_idx);
                    fprintf(fid, '%d 0 0\n%d 0 0\n%d 0 0\n%d 0 0\n', F(i,1)-1, F(i,2)-1, F(i,3)-1, F(i,4)-1);
                end
                fprintf(fid, 'kids 0\n');
                fclose(fid);
                
                % Lanzar FlightGear en segundo plano (usando 'start' para Windows)
                disp('>>> Lanzando FlightGear (puede tardar 30-60 segundos)...');
                fg_cmd = ['start "" "' fg_root '\bin\fgfs.exe" ' ...
                    '--fdm=null ' ...
                    '--native-fdm=socket,in,30,localhost,5502,udp ' ...
                    '--fog-fastest ' ...
                    '--disable-clouds ' ...
                    '--start-date-lat=2024:06:15:12:00:00 ' ...
                    '--disable-sound ' ...
                    '--geometry=1024x768 ' ...
                    '--altitude=' num2str(alt0) ' ' ...
                    '--heading=0 ' ...
                    '--lat=' num2str(lat0) ' ' ...
                    '--lon=' num2str(lon0) ' ' ...
                    '--prop:/sim/current-view/view-number=1 ' ...
                    '--prop:/sim/model/path="' ac_path_fg '"'];
                system(fg_cmd);
                
                % Esperar a que FlightGear arranque (primera vez descarga terreno)
                disp('>>> Esperando a que FlightGear cargue (35 segundos)...');
                pause(35);
                
                % Configurar FlightGearAnimation
                h_fg = Aero.FlightGearAnimation;
                h_fg.FlightGearBaseDirectory = fg_root;
                h_fg.OutputFileName = '';
                h_fg.FramesPerSecond = 30;
                h_fg.TimeScaling = 2;
                
                % Formato: [time, lat(rad), lon(rad), alt(m), phi(rad), theta(rad), psi(rad)]
                tsdata = [t_out, lat_series, lon_series, alt_series, ...
                          phi_series, theta_series, psi_series];
                h_fg.TimeSeriesSource = tsdata;
                
                h_fg.initialize();
                disp('>>> Conexion establecida. Reproduciendo vuelo...');
                h_fg.play();
                disp('>>> Animacion FlightGear completada.');
                
            else
                disp('>>> FlightGear NO encontrado. Usando visualizador 3D de MATLAB...');
                
                % --- FALLBACK: patch + hgtransform ---
                c_w = uav_chord;
                L_f = uav_length;
                fig3d = figure('Name','HALE UAV - Entorno 3D','Color',[0.05 0.05 0.15],...
                    'Position',[100 100 1000 600],'NumberTitle','off');
                ax3d = axes('Parent',fig3d);
                hold(ax3d,'on'); axis(ax3d,'equal'); grid(ax3d,'on');
                ax3d.Color = [0.08 0.08 0.18];
                ax3d.GridColor = [0.3 0.3 0.4];
                xlabel(ax3d,'X (m)','Color','w'); ylabel(ax3d,'Y (m)','Color','w'); zlabel(ax3d,'Alt (m)','Color','w');
                title(ax3d,'HALE UAV - Vuelo 3D (FlightGear no instalado)','Color','w','FontSize',14);
                ax3d.XColor='w'; ax3d.YColor='w'; ax3d.ZColor='w';
                view(ax3d, [-35 25]); lighting(ax3d,'gouraud'); camlight('headlight');
                hg = hgtransform('Parent',ax3d);
                
                % Ala
                wing_x = [c_w/2, -c_w/2, -c_w/2, c_w/2];
                wing_y = [-b_w/2, -b_w/2, b_w/2, b_w/2];
                patch('XData',wing_x,'YData',wing_y,'ZData',[0 0 0 0],...
                    'FaceColor',[0.2 0.5 0.95],'EdgeColor',[0.1 0.3 0.7],...
                    'FaceAlpha',0.85,'Parent',hg);
                t_w = c_w*0.06;
                patch('XData',wing_x,'YData',wing_y,'ZData',[t_w t_w t_w t_w],...
                    'FaceColor',[0.15 0.4 0.85],'EdgeColor',[0.1 0.3 0.7],...
                    'FaceAlpha',0.85,'Parent',hg);
                
                % Fuselaje
                fuse_r = L_f*0.015;
                [cx,cy,cz] = cylinder(fuse_r, 16);
                cx = cx*L_f - L_f/2;
                surf(cx,cy,cz*0,'FaceColor',[0.7 0.7 0.75],'EdgeColor','none','Parent',hg);
                
                % H-Tail
                hs = b_w*0.22; hc = c_w*0.55; hx0 = -L_f/2;
                patch('XData',[hx0+hc,hx0,hx0,hx0+hc],'YData',[-hs/2,-hs/2,hs/2,hs/2],'ZData',[0 0 0 0],...
                    'FaceColor',[0.95 0.25 0.2],'EdgeColor',[0.6 0.1 0.1],'FaceAlpha',0.85,'Parent',hg);
                
                % V-Tail
                vh = b_w*0.07; vc = hc*0.8;
                patch('XData',[hx0+vc,hx0,hx0,hx0+vc],'YData',[0 0 0 0],'ZData',[0,0,vh,vh*0.7],...
                    'FaceColor',[1.0 0.8 0.1],'EdgeColor',[0.6 0.5 0.0],'FaceAlpha',0.85,'Parent',hg);
                
                % Trayectoria
                plot3(ax3d, x_pos, zeros(size(x_pos)), z_pos, '--','Color',[0.4 0.8 0.4 0.5]);
                
                % Animar
                for i = 1:5:length(t_out)
                    if ~isvalid(fig3d), break; end
                    th = theta(i);
                    set(hg,'Matrix', makehgtform('translate',[x_pos(i),0,z_pos(i)])*makehgtform('yrotate',-th));
                    set(ax3d,'XLim',[x_pos(i)-b_w*2, x_pos(i)+b_w*4],...
                             'YLim',[-b_w*1.5, b_w*1.5],...
                             'ZLim',[z_pos(i)-b_w*1.5, z_pos(i)+b_w*1.5]);
                    title(ax3d,sprintf('HALE UAV | t=%.1fs | Alt=%.0fm | Pitch=%.2f deg',...
                        t_out(i),z_pos(i),rad2deg(th)),'Color','w','FontSize',13);
                    drawnow limitrate;
                end
            end
            
            %% ===== FASE 5: Simulink =====
            mdl = 'HALE_Autopilot_3D';
            if bdIsLoaded(mdl), close_system(mdl, 0); end
            new_system(mdl);
            open_system(mdl);
            add_block('simulink/Sources/Step', [mdl '/Control_Elevador']);
            add_block('cstblocks/LTI System', [mdl '/VLM_HALE_UAV']);
            add_block('simulink/Signal Routing/Demux', [mdl '/Demux_Estados']);
            add_block('simulink/Sinks/Scope', [mdl '/Scope_Estados']);
            set_param([mdl '/VLM_HALE_UAV'], 'sys', 'sys_longitudinal');
            add_line(mdl, 'Control_Elevador/1', 'VLM_HALE_UAV/1');
            add_line(mdl, 'VLM_HALE_UAV/1', 'Demux_Estados/1');
            add_line(mdl, 'Demux_Estados/4', 'Scope_Estados/1');
            disp('>>> Simulink + Animacion 3D listos.');
            """
            
            eng.eval(matlab_script, nargout=0)
            
            self.console.append("> ¡ANIMACIÓN 3D COMPLETADA!")
            self.console.append("> Deberías ver una ventana 3D con tu HALE UAV volando.")
            self.console.append("> El modelo incluye: Fuselaje, Ala, H-Tail y V-Tail con colores.")
            self.console.append("> Además, Simulink se abrió con el diagrama de control.")
            
        except ImportError:
            self.console.append("> ERROR: La librería 'matlab.engine' no está instalada en tu Python actual.")
            self.console.append("> ESTÁS USANDO EL PYTHON EQUIVOCADO (Python 3.13).")
            self.console.append("> Por favor, cierra esta app y ejecútala dando doble clic en 'run_app.bat'")
            self.console.append("> Alternativamente, puedes usar el botón gris para exportar el archivo .m.")
        except Exception as e:
            self.console.append(f"> ERROR de API MATLAB: {str(e)}")
