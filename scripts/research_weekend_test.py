import pandas as pd
import requests
import time
from datetime import datetime, timedelta

SYMBOLS = ["NOTUSDT", "DOGEUSDT", "SHIBUSDT", "1000SATSUSDT"]
INTERVAL = "1m"
BASE_URL = "https://api.binance.com/api/v3/klines"

def get_binance_data(symbol, interval, start_time=None, limit=1000):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    if start_time:
        params["startTime"] = start_time
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_recent_data(symbol, days=4):
    start_ts = int((time.time() - (days * 24 * 3600)) * 1000)
    full_data = []
    last_ts = start_ts
    while True:
        data = get_binance_data(symbol, INTERVAL, start_time=last_ts, limit=1000)
        if not data:
            break
        full_data.extend(data)
        last_ts = data[-1][0] + 1
        if len(data) < 1000:
            break
        time.sleep(0.1)
    
    df = pd.DataFrame(full_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 
        'close_time', 'qav', 'not', 'tbbav', 'tbqav', 'ignore'
    ])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    return df

def test_weekend_v4(symbol, allow_long=True):
    df = get_recent_data(symbol, days=5) # 5 días atrás para asegurar margen de cálculo
    if df.empty:
        return None
    
    # Indicadores
    df['vol_mean'] = df['volume'].rolling(window=1440).mean()
    df['vol_std'] = df['volume'].rolling(window=1440).std()
    df['z_score'] = (df['volume'] - df['vol_mean']) / df['vol_std']
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Filtro del finde: Viernes 17, Sab 18, Dom 19 (UTC)
    # Definimos el finde desde el viernes 17 de abril a las 00:00
    weekend_start = pd.to_datetime('2026-04-17 00:00:00')
    
    # Parámetros del Fino V4
    Z_THRESHOLD = 10.0
    RSI_ENTRY_MAX = 65
    RSI_SHORT_MIN = 88
    
    in_position = False
    pos_type = None 
    entry_price = 0
    trades = []
    
    for i in range(1440, len(df)):
        row = df.iloc[i]
        
        # Ignorar señales antes del fin de semana
        if row['date'] < weekend_start:
            continue
            
        if not in_position:
            if allow_long and row['z_score'] > Z_THRESHOLD and row['rsi'] < RSI_ENTRY_MAX:
                in_position = True
                pos_type = 'long'
                entry_price = row['close']
                entry_date = row['date']
            elif row['rsi'] > RSI_SHORT_MIN:
                in_position = True
                pos_type = 'short'
                entry_price = row['close']
                entry_date = row['date']
        else:
            if pos_type == 'long':
                profit = (row['close'] - entry_price) / entry_price * 100
                if row['rsi'] > 85 or profit >= 8.0 or profit <= -4.0:
                    trades.append({
                        'type': 'long', 
                        'profit': profit,
                        'entry': entry_date,
                        'exit': row['date']
                    })
                    in_position = False
            else:
                profit = (entry_price - row['close']) / entry_price * 100
                if row['rsi'] < 45 or profit >= 5.0 or profit <= -3.0:
                    trades.append({
                        'type': 'short', 
                        'profit': profit,
                        'entry': entry_date,
                        'exit': row['date']
                    })
                    in_position = False
                
    if not trades:
        return {'symbol': symbol, 'net_profit': 0, 'trades': 0, 'details': []}

    tdf = pd.DataFrame(trades)
    return {
        'symbol': symbol,
        'net_profit': tdf['profit'].sum(),
        'trades': len(tdf),
        'long_profit': tdf[tdf['type']=='long']['profit'].sum() if 'long' in tdf['type'].values else 0,
        'short_profit': tdf[tdf['type']=='short']['profit'].sum() if 'short' in tdf['type'].values else 0,
        'win_rate': (tdf['profit'] > 0).mean() * 100,
        'details': trades
    }

if __name__ == "__main__":
    out_lines = []
    out_lines.append("=== BUSCANDO LA CUARTA MONEDA (TEST FINDESEMANA) ===")
    for s in SYMBOLS:
        out_lines.append(f"\nDescargando y analizando {s}...")
        res = test_weekend_v4(s, allow_long=True)
        if not res:
            out_lines.append(f"Error procesando {s}")
            continue
        title = f"{s} (DUAL)"
        out_lines.append(f"--- {title} ---")
        out_lines.append(f" Net Profit: {res['net_profit']:.2f}%")
        out_lines.append(f" WinRate: {res['win_rate']:.1f}% ({res['trades']} trades)")
        if res['trades'] > 0:
            for t in res['details']:
                out_lines.append(f"   [{t['type'].upper()}] Entry: {t['entry']} | Exit: {t['exit']} | Profit: {t['profit']:.2f}%")
    
    with open(r"C:\CHACAL_ZERO_FRICTION\research_data\candidates_summary.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    print("Guardado en candidates_summary.txt")
