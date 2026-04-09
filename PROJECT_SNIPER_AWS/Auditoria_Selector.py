
import pandas as pd
import numpy as np
import os

DATA_PATH = r'user_data/data/binance/futures'

def ema_pure(series, period=50):
    return series.ewm(span=period, adjust=False).mean()

def atr_pure(df, period=14):
    tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def rsi_pure(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0); down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    return 100 - (100 / (1 + (ema_up / ema_down)))

def auditar_selector():
    print("📡 Extrayendo datos crudos del Bitcoin para Auditoría...")
    
    # 1. Cargar BTC
    file_path = os.path.join(DATA_PATH, "BTC_USDT_USDT-1h-futures.feather")
    df = pd.read_feather(file_path)
    df.columns = [c.lower() for c in df.columns]
    df['date'] = pd.to_datetime(df['date'], utc=True)
    
    # 2. Filtrar solo Mayo (Lateral) y Agosto (Crash)
    df = df[(df['date'].dt.month.isin([5, 8])) & (df['date'].dt.year == 2024)].copy()
    
    # 3. Aplicar los indicadores EXACTOS de ChacalTripleMode.py
    df['ema50'] = ema_pure(df['close'], 50)
    df['atr_btc'] = atr_pure(df, 14)
    df['atr_btc_mean'] = df['atr_btc'].rolling(8).mean()
    df['rsi_btc_1h'] = rsi_pure(df['close'], 14)
    
    # 4. Construir la lógica exacta de cambio de modo
    # (El Master Switch de Bear44)
    btc_under_ema50 = df['close'] < df['ema50']
    btc_vol_activa  = df['atr_btc'] > df['atr_btc_mean']
    df['master_bear_switch'] = (btc_under_ema50 & btc_vol_activa).astype(int)

    # Umbrales que estaban fijos en la estrategia (40 y 25)
    bear_thresh = 40
    sb_thresh = 20

    df['MODO_ACTIVO'] = "MODO 0 (Fuera)"
    
    # MODO 1: Lateral Bear
    df.loc[(df['master_bear_switch'] == 1) & (df['rsi_btc_1h'] >= bear_thresh), 'MODO_ACTIVO'] = "MODO 1 (LATERAL BEAR)"
    
    # MODO 2: Bear Normal
    df.loc[(df['master_bear_switch'] == 1) & (df['rsi_btc_1h'] < bear_thresh) & (df['rsi_btc_1h'] >= sb_thresh), 'MODO_ACTIVO'] = "MODO 2 (BEAR NORMAL)"
    
    # MODO 3: Super Bear
    df.loc[(df['master_bear_switch'] == 1) & (df['rsi_btc_1h'] < sb_thresh), 'MODO_ACTIVO'] = "MODO 3 (SUPER BEAR)"

    # Limpiar tabla para exportación
    reporte = df[['date', 'close', 'ema50', 'rsi_btc_1h', 'atr_btc', 'atr_btc_mean', 'MODO_ACTIVO']].copy()
    reporte.rename(columns={'close': 'BTC_PRECIO', 'rsi_btc_1h': 'RSI_BTC'}, inplace=True)
    
    # Exportar a CSV para el Capitán
    csv_path = "Radiografia_Selector.csv"
    reporte.to_csv(csv_path, index=False)
    
    print(f"\n✅ DATOS CRUDOS EXPORTADOS: Se creó el archivo {csv_path} en tu carpeta.")
    print("\nResumen Rápido (Cantidad de horas que el bot pasó en cada modo):")
    
    # Mayo
    print("\n📊 MES DE MAYO (Supuesto Lateral):")
    mayo = reporte[reporte['date'].dt.month == 5]
    print(mayo['MODO_ACTIVO'].value_counts())
    
    # Agosto
    print("\n📊 MES DE AGOSTO (Crash):")
    agosto = reporte[reporte['date'].dt.month == 8]
    print(agosto['MODO_ACTIVO'].value_counts())

if __name__ == "__main__":
    auditar_selector()
