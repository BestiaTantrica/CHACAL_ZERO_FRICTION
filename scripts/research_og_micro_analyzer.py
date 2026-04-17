import pandas as pd
import numpy as np
import os

# Configuración
FILE_1M = r"C:\CHACAL_ZERO_FRICTION\research_data\OGUSDT_1m_recent.csv"
EVENT_DATE = "2026-04-14 14:00:00" # Primer gran pump reciente

def analyze_micro_footprint():
    if not os.path.exists(FILE_1M):
        print(f"Error: No se encuentra el archivo 1m en {FILE_1M}")
        return

    print(f"--- ANALISIS MICRO (1m) - EVENTO: {EVENT_DATE} ---")
    df = pd.read_csv(FILE_1M)
    df['date'] = pd.to_datetime(df['date'])
    
    # Buscamos la fila del evento
    event_idx = df[df['date'] == EVENT_DATE].index
    if event_idx.empty:
        print("Evento no encontrado en la data de 1m descargada.")
        return
    
    idx = event_idx[0]
    
    # 1. Ventana de Estudio: 3 horas antes (180 min) y 1 hora durante (60 min)
    start_idx = max(0, idx - 180)
    end_idx = min(len(df), idx + 60)
    window = df.iloc[start_idx:end_idx].copy()
    
    # 2. Análisis de Pre-Volumen
    # Calculamos la media de volumen de las últimas 24 horas previas al bloque de estudio
    pre_event_vol_mean = df.iloc[idx-1440:idx-180]['volume'].mean()
    
    print(f"\nHuella de Volumen (120 min antes del estallido):")
    for offset in [120, 60, 30, 10]:
        vol_in_segment = df.iloc[idx-offset:idx-offset+10]['volume'].mean()
        ratio = vol_in_segment / pre_event_vol_mean
        print(f" - T minus {offset} min: Volumen {ratio:.2f}x respecto a la media diaria.")

    # 3. Análisis de Acción del Precio (Squeeze)
    df['range'] = df['high'] - df['low']
    pre_event_range = df.iloc[idx-180:idx-10]['range'].mean()
    event_range = df.iloc[idx:idx+10]['range'].mean()
    
    print(f"\nSqueeze de Volatilidad:")
    print(f" - Rango promedio 3h antes: {pre_event_range:.4f}")
    print(f" - Rango promedio al estallar (10m): {event_range:.4f} ({event_range/pre_event_range:.1f}x expansion)")

    # 4. ¿Hubo "Velas de Aviso"?
    # Buscamos si en los 30 min previos hubo alguna vela con volumen > 3x media sin mover el precio
    avisos = df.iloc[idx-30:idx][(df['volume'] > pre_event_vol_mean * 3)]
    if not avisos.empty:
        print(f"\nDETECTOR DE AVISOS: Se detectaron {len(avisos)} velas de volumen anómalo en los 30m previos.")
    else:
        print("\nDETECTOR DE AVISOS: No hubo anomalías claras. El estallido fue súbito.")

if __name__ == "__main__":
    analyze_micro_footprint()
