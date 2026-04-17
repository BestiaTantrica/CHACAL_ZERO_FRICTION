import pandas as pd
import numpy as np
import os

DATA_DIR = r"C:\CHACAL_ZERO_FRICTION\research_data"

def backtest_arena_v4(symbol):
    file_path = os.path.join(DATA_DIR, f"{symbol}_1m_recent.csv")
    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # 1. Indicadores (Fino de Producción)
    df['vol_mean'] = df['volume'].rolling(window=1440).mean()
    df['vol_std'] = df['volume'].rolling(window=1440).std()
    df['z_score'] = (df['volume'] - df['vol_mean']) / df['vol_std']
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Parámetros del Fino
    Z_THRESHOLD = 10.0
    RSI_ENTRY_MAX = 65
    RSI_SHORT_MIN = 88
    
    # 2. Simulación
    in_position = False
    pos_type = None 
    entry_price = 0
    trades = []
    
    for i in range(1440, len(df)):
        row = df.iloc[i]
        
        if not in_position:
            # LONG: Ignición extrema + Espacio para correr (RSI bajo)
            if row['z_score'] > Z_THRESHOLD and row['rsi'] < RSI_ENTRY_MAX:
                in_position = True
                pos_type = 'long'
                entry_price = row['close']
                entry_date = row['date']
            
            # SHORT: Agotamiento final
            elif row['rsi'] > RSI_SHORT_MIN:
                in_position = True
                pos_type = 'short'
                entry_price = row['close']
                entry_date = row['date']
        else:
            if pos_type == 'long':
                profit = (row['close'] - entry_price) / entry_price * 100
                # Salida: RSI Agotado o 8% TP o 4% SL
                if row['rsi'] > 85 or profit >= 8.0 or profit <= -4.0:
                    trades.append({'type': 'long', 'profit': profit})
                    in_position = False
            else:
                profit = (entry_price - row['close']) / entry_price * 100
                # Salida: Reversión a la media (RSI 45) o 5% TP o 3% SL
                if row['rsi'] < 45 or profit >= 5.0 or profit <= -3.0:
                    trades.append({'type': 'short', 'profit': profit})
                    in_position = False
                
    if not trades:
        return None

    tdf = pd.DataFrame(trades)
    return {
        'symbol': symbol,
        'net_profit': tdf['profit'].sum(),
        'trades': len(tdf),
        'long_profit': tdf[tdf['type']=='long']['profit'].sum(),
        'short_profit': tdf[tdf['type']=='short']['profit'].sum(),
        'win_rate': (tdf['profit'] > 0).mean() * 100
    }

if __name__ == "__main__":
    # Solo OG y SANTOS por ahora (LAZIO/ALPINE en descarga)
    symbols = ["OGUSDT", "SANTOSUSDT"] 
    print("--- BACKTEST FINO V4 (PARAMETROS PRODUCCIÓN) ---")
    for s in symbols:
        res = backtest_arena_v4(s)
        if res:
            print(f"\n{s}:")
            print(f" - Net Profit Total: {res['net_profit']:.2f}%")
            print(f" - Profit LONG: {res['long_profit']:.2f}%")
            print(f" - Profit SHORT: {res['short_profit']:.2f}%")
            print(f" - WinRate: {res['win_rate']:.1f}% ({res['trades']} trades)")
