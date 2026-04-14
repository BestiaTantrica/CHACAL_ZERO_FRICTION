import pandas as pd
import numpy as np
import talib.abstract as ta
import json
import os

def analyze_sustos(df, pair_name):
    """
    Analiza 'sustos' (caídas anormales) de forma milimétrica para un par específico.
    """
    print(f"\n--- RADAR DE SUSTOS: {pair_name} ---")
    
    # 1. Medición de Volatilidad Relativa
    df['atr'] = ta.ATR(df, timeperiod=14)
    df['atr_pct'] = df['atr'] / df['close']
    
    # 2. Medición de Retornos (1m)
    df['pct_change'] = df['close'].pct_change()
    
    # 3. Z-Score de Retornos (Detectar outliers estadísticos)
    window = 120 # 2 horas en 1m
    df['mean_ret'] = df['pct_change'].rolling(window=window).mean()
    df['std_ret'] = df['pct_change'].rolling(window=window).std()
    df['z_score'] = (df['pct_change'] - df['mean_ret']) / df['std_ret']
    
    # 4. Volumen Relativo
    df['vol_mean'] = df['volume'].rolling(window=20).mean()
    df['vol_spike'] = df['volume'] / df['vol_mean']
    
    # Filtro de "Susto": Retorno < -3 Desviaciones Estándar Y Volumen > 2x media
    sustos = df[(df['z_score'] < -3) & (df['vol_spike'] > 2)].copy()
    
    if not sustos.empty:
        print(f"Detectados {len(sustos)} micro-sustos en el periodo.")
        # Ver el rebote promedio a los 10 minutos
        rebotes = []
        for idx in sustos.index:
            if idx + 10 < len(df):
                price_at_susto = df.loc[idx, 'close']
                price_after_10m = df.loc[idx+10, 'close']
                rebote = (price_after_10m - price_at_susto) / price_at_susto
                rebotes.append(rebote)
        
        if rebotes:
            print(f"Rebote promedio (10 min): {np.mean(rebotes)*100:.2f}%")
            print(f"Mejor rebote: {np.max(rebotes)*100:.2f}%")
            print(f"WinRate de Rebote (>0%): {len([r for r in rebotes if r > 0])/len(rebotes)*100:.1f}%")
    else:
        print("No se detectaron sustos con los umbrales actuales.")

if __name__ == "__main__":
    # Intenta cargar datos de ejemplo si existen
    data_path = "user_data/data/binance/LTC_USDT-1m.json" # Ejemplo
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            data = json.load(f)
            df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            analyze_sustos(df, "LTC/USDT")
    else:
        print(f"No se encontró archivo de datos en {data_path}. Ejecuta descarga de datos primero.")
