import pandas as pd
import numpy as np
import os

DATA_DIR = r"C:\CHACAL_ZERO_FRICTION\research_data"

def run_resampled_backtest(symbol, timeframe='5min'):
    file_path = os.path.join(DATA_DIR, f"{symbol}_1m_recent.csv")
    if not os.path.exists(file_path):
        return None

    df_1m = pd.read_csv(file_path)
    df_1m['date'] = pd.to_datetime(df_1m['date'])
    df_1m.set_index('date', inplace=True)
    
    # Resample a 5m
    df = df_1m.resample(timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    df.reset_index(inplace=True)
    
    # Indicadores
    df['vol_mean'] = df['volume'].rolling(window=288).mean() # 288 candles of 5m = 24h
    df['vol_std'] = df['volume'].rolling(window=288).std()
    df['z_score'] = (df['volume'] - df['vol_mean']) / df['vol_std']
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Simulación (Mismos parámetros que V4)
    in_position = False
    pos_type = None 
    entry_price = 0
    trades = []
    
    for i in range(288, len(df)):
        row = df.iloc[i]
        
        if not in_position:
            if row['z_score'] > 10.0 and row['rsi'] < 65:
                in_position = True
                pos_type = 'long'
                entry_price = row['close']
            elif row['rsi'] > 88:
                in_position = True
                pos_type = 'short'
                entry_price = row['close']
        else:
            if pos_type == 'long':
                profit = (row['close'] - entry_price) / entry_price * 100
                if row['rsi'] > 85 or profit >= 8.0 or profit <= -4.0:
                    trades.append({'profit': profit})
                    in_position = False
            else:
                profit = (entry_price - row['close']) / entry_price * 100
                if row['rsi'] < 45 or profit >= 5.0 or profit <= -3.0:
                    trades.append({'profit': profit})
                    in_position = False
                    
    if not trades:
        return 0, 0
        
    tdf = pd.DataFrame(trades)
    return tdf['profit'].sum(), len(tdf)

if __name__ == "__main__":
    symbol = "SANTOSUSDT"
    print(f"--- COMPARATIVA 1m vs 5m: {symbol} ---")
    
    prof_1m, t_1m = run_resampled_backtest(symbol, timeframe='1min')
    prof_5m, t_5m = run_resampled_backtest(symbol, timeframe='5min')
    
    print(f"\nResultados 1m:")
    print(f" - Net Profit: {prof_1m:.2f}%")
    print(f" - Trades: {t_1m}")
    
    print(f"\nResultados 5m:")
    print(f" - Net Profit: {prof_5m:.2f}%")
    print(f" - Trades: {t_5m}")
    
    if prof_1m > prof_5m:
        print(f"\nConclusion: 1m es mejor por {prof_1m - prof_5m:.2f}%")
    else:
        print(f"\nConclusion: 5m es mejor por {prof_5m - prof_1m:.2f}%")
