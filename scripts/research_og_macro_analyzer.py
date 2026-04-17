import pandas as pd
import numpy as np
import os

# Configuración
FILE_1H = r"C:\CHACAL_ZERO_FRICTION\research_data\OGUSDT_1h_full.csv"
CANDIDATES_FILE = r"C:\CHACAL_ZERO_FRICTION\research_data\OGUSDT_pump_candidates.csv"

def analyze_macro_pumps():
    if not os.path.exists(FILE_1H):
        print("Error: No se encuentra el archivo historial 1h.")
        return

    df = pd.read_csv(FILE_1H)
    df['date'] = pd.to_datetime(df['date'])
    
    # 1. Re-identificación de Pumps con métricas de "Post-Pump" (Reversión)
    # Definimos Pump como vela con high > 7% del open
    df['pump_magnitude'] = (df['high'] - df['open']) / df['open'] * 100
    pumps = df[df['pump_magnitude'] >= 7].copy()
    
    print(f"--- ANÁLISIS MACRO DE 46,000 HORAS (OG/USDT) ---")
    print(f"Total de Pumps detectados (>7%): {len(pumps)}")
    
    # 2. Análisis de Reversión (¿Qué pasa después?)
    # Miramos el cierre 4 horas después
    reversiones = []
    for idx in pumps.index:
        if idx + 4 < len(df):
            price_at_pump_high = df.loc[idx, 'high']
            price_after_4h = df.loc[idx+4, 'close']
            reversion = (price_after_4h - price_at_pump_high) / price_at_pump_high * 100
            reversiones.append(reversion)
            
    print(f"\nESTADISTICAS DE IMPACTO:")
    print(f" - Magnitud promedio del Pump: {pumps['pump_magnitude'].mean():.2f}%")
    print(f" - Magnitud máxima registrada: {pumps['pump_magnitude'].max():.2f}%")
    print(f" - Reversión promedio (a las 4h desde el pico): {np.mean(reversiones):.2f}%")
    
    # 3. Estacionalidad (Día de la semana)
    pumps['day_name'] = pumps['date'].dt.day_name()
    day_counts = pumps['day_name'].value_counts()
    print(f"\nRECURRENCIA POR DIA:")
    print(day_counts)
    
    # 4. Concentración Temporal (Clusters)
    # ¿Vienen solos o en manada?
    pumps['time_diff'] = pumps['date'].diff().dt.total_seconds() / 3600
    clusters = pumps[pumps['time_diff'] < 24]
    print(f"\nCOMPORTAMIENTO EN CADENA (CLUSTERS):")
    print(f" - El {len(clusters)/len(pumps)*100:.1f}% de los pumps ocurren en menos de 24h de diferencia con el anterior.")
    print(f" - Esto indica que cuando OG despierta, suele tener múltiples oleadas (como vimos el 14 de Abril).")

    # 5. Guardar candidatos refinados para estudio 1m
    pumps.to_csv(CANDIDATES_FILE, index=False)
    print(f"\n[OK] Candidatos actualizados en {CANDIDATES_FILE}")

if __name__ == "__main__":
    analyze_macro_pumps()
