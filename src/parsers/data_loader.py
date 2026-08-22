import pandas as pd
import os

class DataLoader:
    def __init__(self):
        self.atmosfera_df = None
        self.aerodinamica_df = None
        
    def cargar_atmosfera(self, filepath="data/Atmosfera estandar.csv"):
        """
        Carga el archivo de Atmósfera Estándar.
        Salta las filas 1 y 2 que contienen los símbolos y las unidades.
        """
        try:
            # skiprows=[1, 2] salta la fila de símbolos (- h -) y la de unidades ((m))
            if filepath.endswith('.csv'):
                self.atmosfera_df = pd.read_csv(filepath, skiprows=[1, 2], encoding='latin1')
            elif filepath.endswith(('.xls', '.xlsx')):
                self.atmosfera_df = pd.read_excel(filepath, skiprows=[1, 2])
            else:
                raise ValueError("Formato de archivo no soportado. Use CSV o Excel.")
            
            # Limpiar nombres de columnas (quitar espacios en blanco al inicio/final)
            self.atmosfera_df.columns = self.atmosfera_df.columns.str.strip()
            return True, "Atmósfera cargada automáticamente."
        except Exception as e:
            return False, f"Error al cargar atmósfera: {str(e)}"
            
    def cargar_aerodinamica(self, filepath="data/Aerodinamica.csv"):
        """
        Carga el archivo de Aerodinámica Inicial.
        Salta la fila 1 que contiene los símbolos de las variables.
        """
        try:
            # skiprows=[1] salta la fila de símbolos (alpha, CL, CD ala, etc.)
            if filepath.endswith('.csv'):
                self.aerodinamica_df = pd.read_csv(filepath, skiprows=[1], encoding='latin1')
            elif filepath.endswith(('.xls', '.xlsx')):
                self.aerodinamica_df = pd.read_excel(filepath, skiprows=[1])
            else:
                raise ValueError("Formato de archivo no soportado. Use CSV o Excel.")
            
            self.aerodinamica_df.columns = self.aerodinamica_df.columns.str.strip()
            return True, "Aerodinámica cargada automáticamente."
        except Exception as e:
            return False, f"Error al cargar aerodinámica: {str(e)}"
    
    def get_atmosfera_data(self):
        return self.atmosfera_df
        
    def get_aerodinamica_data(self):
        return self.aerodinamica_df
