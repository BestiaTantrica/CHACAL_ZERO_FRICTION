
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

# =========================================================================
# LECTOR DE FEATHER (Ajustado a tus archivos reales con FIX de Timezone)
# =========================================================================

def rsi_pure(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

def atr_pure(df, period=14):
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def ema_pure(series, period=50):
    return series.ewm(span=period, adjust=False).mean()

DATA_PATH = r'user_data/data/binance/futures'

def cargar_datos(pair, timeframe='5m', timerange='20240801-20240901'):
    filename = f"{pair.replace('/', '_').replace(':', '_')}-{timeframe}-futures.feather"
    full_path = os.path.join(DATA_PATH, filename)
    
    if os.path.exists(full_path):
        print(f"✅ Archivo [FEATHER] encontrado: {filename}")
        try:
            df = pd.read_feather(full_path)
            df.columns = [c.lower() for c in df.columns]
            
            # -- FIX TIMEZONE --
            df['date'] = pd.to_datetime(df['date'], utc=True)
            
            # Filtrar por timerange con UTC activado
            start_ts = pd.to_datetime(timerange.split('-')[0], utc=True)
            end_ts = pd.to_datetime(timerange.split('-')[1], utc=True)
            
            df = df[(df['date'] >= start_ts) & (df['date'] <= end_ts)]
            return df
        except Exception as e:
            print(f"❌ ERROR al leer Feather: {e}")
            return None
            
    print(f"❌ ERROR: No se encontró {filename}")
    return None

def diagnostico():
    print("\n🦅 --- DIAGNÓSTICO FEATHER CHACAL (FIX TIMEZONE) ---")
    
    btc_1h = cargar_datos("BTC/USDT:USDT", timeframe="1h")
    if btc_1h is None: return

    pair_test = "SOL/USDT:USDT"
    df = cargar_datos(pair_test, timeframe="5m")
    if df is None: return

    print("🧠 Procesando motor de señales...")
    df['rsi'] = rsi_pure(df['close'], 14)
    df['atr'] = atr_pure(df, 14)
    df['price_change'] = df['close'].pct_change()
    df['bb_middleband'] = df['close'].rolling(20).mean()

    btc_1h['ema50'] = ema_pure(btc_1h['close'], 50)
    btc_1h['atr_btc'] = atr_pure(btc_1h, 14)
    btc_1h['atr_btc_mean'] = btc_1h['atr_btc'].rolling(8).mean()
    btc_1h['rsi_btc_1h'] = rsi_pure(btc_1h['close'], 14)
    
    df_btc = btc_1h[['date', 'close', 'ema50', 'rsi_btc_1h', 'atr_btc', 'atr_btc_mean']].copy()
    df_btc = df_btc.rename(columns={'close': 'btc_close', 'ema50': 'btc_ema50'})
    df = pd.merge(df, df_btc, on='date', how='left').ffill()

    df['btc_under_ema50'] = (df['btc_close'] < df['btc_ema50']).astype(int)
    df['btc_vol_activa']  = (df['atr_btc'] > df['atr_btc_mean']).astype(int)
    df['master_bear_switch'] = (df['btc_under_ema50'] & df['btc_vol_activa'])
    
    pulse = 0.001 
    v_factor = 1.44
    df['vol_mean'] = df['volume'].rolling(20).mean()
    
    df['base_cond'] = (
        (df['price_change'] < -pulse) & 
        (df['close'] < df['bb_middleband']) & 
        (df['rsi'] < 45)
    ).astype(int)

    # Evaluación de señales
    df['enter_bear'] = (df['base_cond'] == 1) & (df['rsi_btc_1h'] < 40) & (df['master_bear_switch'] == 1) & (df['volume'] > df['vol_mean'] * v_factor)
    
    total_v = len(df)
    switch_on = df['master_bear_switch'].sum()
    entradas = df['enter_bear'].sum()
    
    print("\n--- REPORTE FINAL ---")
    print(f"📡 Velas analizadas: {total_v}")
    print(f"🏹 Master Switch activo: {switch_on} veces")
    print(f"🚀 Señales de SHORT encontradas: {entradas}")
    
    if entradas > 0:
        print("\n✅ VICTORIA COMPLETA: El motor ve los datos y genera señales.")
        print("Muestra de señales:")
        print(df[df['enter_bear']][['date', 'price_change', 'rsi', 'btc_close']].head(10))
    else:
        print("\n❌ CERO SEÑALES: Los filtros son muy estrictos (Pulse/Volume/RSI).")

if __name__ == "__main__":
    diagnostico()
