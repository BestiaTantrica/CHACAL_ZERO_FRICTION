import ccxt
import pandas as pd
import numpy as np
import os
# removed unused import
from datetime import datetime, timedelta, timezone
import talib.abstract as ta

# CONFIGURACIÓN
SYMBOL = 'BTC/USDT'
TIMEFRAMES = ['1m', '1h']
LATERAL_THRESHOLD = 0.039  # 3.9%
MIN_SLICE_DURATION = 120   # 2 horas en velas de 1m
DAYS_BACK = 30
OUTPUT_PAIR = 'BTC_FRANKEN'
DATA_DIR = 'PROJECT_SNIPER_AWS/user_data/data'

exchange = ccxt.binance({'options': {'defaultType': 'future'}})

def fetch_ohlcv(symbol, timeframe, since):
    print(f"Descargando {timeframe} para {symbol} desde {datetime.fromtimestamp(since/1000)}...")
    all_ohlcv = []
    while since < exchange.milliseconds():
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit=1000)
        if not ohlcv:
            break
        since = ohlcv[-1][0] + 1
        all_ohlcv += ohlcv
        if len(ohlcv) < 1000:
            break
    df = pd.DataFrame(all_ohlcv, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'], unit='ms')
    return df

def generate_frankenstein():
    # 1. Calcular puntos de inicio
    now = datetime.now(timezone.utc)
    since = int((now - timedelta(days=DAYS_BACK)).timestamp() * 1000)

    # 2. Descargar datos
    df_1h = fetch_ohlcv(SYMBOL, '1h', since - (100 * 3600 * 1000)) # Extra para EMA50
    df_1m = fetch_ohlcv(SYMBOL, '1m', since)

    # 3. Calcular EMA50 en 1h
    df_1h['ema50'] = ta.EMA(df_1h, timeperiod=50)
    
    # 4. Mapear EMA50 1h a 1m (merge_asof)
    df_1m = pd.merge_asof(
        df_1m.sort_values('date'), 
        df_1h[['date', 'ema50']].sort_values('date'), 
        on='date', 
        direction='backward'
    )

    # 5. Identificar periodos laterales
    df_1m['dist'] = (df_1m['close'] - df_1m['ema50']) / df_1m['ema50']
    df_1m['is_lateral'] = (df_1m['dist'].abs() <= LATERAL_THRESHOLD).astype(int)

    # 6. Agrupar bloques continuos
    df_1m['group'] = (df_1m['is_lateral'] != df_1m['is_lateral'].shift()).cumsum()
    
    slices = []
    for g, data in df_1m[df_1m['is_lateral'] == 1].groupby('group'):
        if len(data) >= MIN_SLICE_DURATION:
            slices.append(data.copy())

    if not slices:
        print("No se encontraron slices laterales consistentes.")
        return

    print(f"Se encontraron {len(slices)} periodos laterales.")

    # 7. Coser el Frankenstein
    frankenstein = pd.concat(slices).reset_index(drop=True)
    
    # 8. Re-indexar timestamps para que sean continuos (1m de intervalo)
    # Empezamos desde una fecha fija o la original del primer slice
    start_date = frankenstein.iloc[0]['date']
    frankenstein['date'] = [start_date + timedelta(minutes=i) for i in range(len(frankenstein))]

    # 9. Guardar en formato Freqtrade (Feather)
    target_file = os.path.join(DATA_DIR, f"{OUTPUT_PAIR}_USDT_USDT-1m-futures.feather")
    
    # Limpiamos columnas extras antes de guardar
    final_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
    frankenstein_final = frankenstein[final_cols]
    
    frankenstein_final.to_feather(target_file)
    print(f"Dataset Frankenstein guardado en: {target_file}")
    print(f"Duración total artificial: {len(frankenstein_final)} minutos (~{len(frankenstein_final)/1440:.2f} días)")

if __name__ == "__main__":
    generate_frankenstein()
