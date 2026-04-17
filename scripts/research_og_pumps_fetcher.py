import requests
import pandas as pd
import os
import time
from datetime import datetime

import sys

# Configuración por defecto
SYMBOLS = ["OGUSDT"]
if len(sys.argv) > 1:
    SYMBOLS = sys.argv[1].split(',')

INTERVAL_MACRO = "1h"
INTERVAL_MICRO = "1m"
DATA_DIR = r"C:\CHACAL_ZERO_FRICTION\research_data"
BASE_URL = "https://api.binance.com/api/v3/klines"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def get_binance_data(symbol, interval, start_time=None, limit=1000):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    if start_time:
        params["startTime"] = start_time
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error en API: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Excepción en petición: {e}")
        return []

def download_full_history(symbol, interval, start_from_days=None):
    print(f"Descargando historial ({interval}) para {symbol}...")
    full_data = []
    
    if start_from_days:
        last_timestamp = int((time.time() - (start_from_days * 24 * 3600)) * 1000)
    else:
        last_timestamp = 0 # Empezar desde el inicio (1970) para pillar todo el historial
    
    while True:
        start_ts = (last_timestamp + 1) if last_timestamp is not None else None
        data = get_binance_data(symbol, interval, start_time=start_ts)
        
        if not data:
            break
            
        full_data.extend(data)
        last_timestamp = data[-1][0]
        
        # Log cada 5000 registros para no inundar
        if len(full_data) % 5000 == 0 or len(data) < 1000:
            print(f" - Recogidos {len(full_data)} registros. Última fecha: {datetime.fromtimestamp(last_timestamp/1000)}")
        
        if len(data) < 1000:
            break
            
        time.sleep(0.1) # Respetar rate limits
        
    df = pd.DataFrame(full_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    
    # Convertir a tipos correctos
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
        
    return df

def main():
    for SYMBOL in SYMBOLS:
        print(f"\n=== PROCESANDO: {SYMBOL} ===")
        # 1. Bajada de 1h (Historia completa)
        df_1h = download_full_history(SYMBOL, INTERVAL_MACRO)
        h1_file = os.path.join(DATA_DIR, f"{SYMBOL}_{INTERVAL_MACRO}_full.csv")
        df_1h.to_csv(h1_file, index=False)
        print(f"Guardado historial 1h en: {h1_file}")
        
        # 2. Análisis rápido de "Pumps"
        df_1h['body_pct'] = (df_1h['close'] - df_1h['open']) / df_1h['open'] * 100
        df_1h['high_pct'] = (df_1h['high'] - df_1h['open']) / df_1h['open'] * 100
        
        pumps = df_1h[(df_1h['body_pct'] > 5) | (df_1h['high_pct'] > 8)].copy()
        print(f"Detectados {len(pumps)} candidatos a Pump en {SYMBOL}.")
        
        pumps_file = os.path.join(DATA_DIR, f"{SYMBOL}_pump_candidates.csv")
        pumps.to_csv(pumps_file, index=False)
        
        # 3. Descarga de los últimos 6 meses en 1m
        print(f"Descargando últimos 180 días en {INTERVAL_MICRO}...")
        df_1m = download_full_history(SYMBOL, INTERVAL_MICRO, start_from_days=180)
        
        m1_file = os.path.join(DATA_DIR, f"{SYMBOL}_{INTERVAL_MICRO}_recent.csv")
        df_1m.to_csv(m1_file, index=False)
        print(f"Guardado historial 1m en: {m1_file}")
    
if __name__ == "__main__":
    main()
