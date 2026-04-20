"""
VERIFICADOR DE INTEGRIDAD DEL BACKTEST
========================================
Reproduce el backtest V3 que dió +316% para ALPINE
y examina los trades individualmente para ver si son reales.
"""
import pandas as pd
import numpy as np
import os

DATA_DIR = r"C:\CHACAL_ZERO_FRICTION\research_data"

def verify_backtest_v3(symbol, max_inspect=10):
    file_path = os.path.join(DATA_DIR, f"{symbol}_1m_recent.csv")
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    df['vol_mean'] = df['volume'].rolling(window=1440).mean()
    df['vol_std'] = df['volume'].rolling(window=1440).std()
    df['z_score'] = (df['volume'] - df['vol_mean']) / df['vol_std']
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    in_position = False
    pos_type = None
    entry_price = 0
    trades = []
    inspected = 0

    for i in range(1440, len(df)):
        row = df.iloc[i]
        
        if not in_position:
            if row['z_score'] > 8.0 and row['rsi'] < 65:
                in_position = True
                pos_type = 'long'
                entry_price = row['close']
                entry_date = row['date']
                entry_idx = i
            elif row['rsi'] > 85:
                in_position = True
                pos_type = 'short'
                entry_price = row['close']
                entry_date = row['date']
                entry_idx = i
        else:
            if pos_type == 'long':
                profit = (row['close'] - entry_price) / entry_price * 100
                if row['rsi'] > 80 or profit >= 8.0 or profit <= -4.0:
                    trade_info = {
                        'type': 'long',
                        'profit': profit,
                        'entry_date': entry_date,
                        'exit_date': row['date'],
                        'entry_price': entry_price,
                        'exit_price': row['close'],
                        'duration_min': i - entry_idx
                    }
                    trades.append(trade_info)
                    
                    # Inspección detallada de los primeros N trades
                    if inspected < max_inspect:
                        t = trade_info
                        print(f"\n  LONG Trade #{inspected+1}:")
                        print(f"    Entry: {t['entry_date']} @ ${t['entry_price']:.4f}")
                        print(f"    Exit:  {t['exit_date']} @ ${t['exit_price']:.4f}")
                        print(f"    Profit: {t['profit']:.2f}% | Duración: {t['duration_min']} min")
                        inspected += 1
                    
                    in_position = False
                    
            else:
                profit = (entry_price - row['close']) / entry_price * 100
                if row['rsi'] < 50 or profit >= 5.0 or profit <= -3.0:
                    trades.append({'type': 'short', 'profit': profit, 'duration_min': i - entry_idx})
                    in_position = False

    tdf = pd.DataFrame(trades)
    print(f"\n--- RESUMEN FINAL {symbol} ---")
    print(f"Total trades: {len(tdf)}")
    print(f"Net Profit: {tdf['profit'].sum():.2f}%")
    print(f"WinRate: {(tdf['profit'] > 0).mean()*100:.1f}%")
    
    print("\nDISTRIBUCIÓN DE TRADES:")
    print(tdf.groupby('type')['profit'].agg(['sum', 'count', 'mean']).round(2))
    
    print("\nDISTRIBUCIÓN DE DURACIÓN (min):")
    print(tdf.groupby('type')['duration_min'].describe().round(1))

if __name__ == "__main__":
    print("=== VERIFICADOR DE INTEGRIDAD DE BACKTEST ===\n")
    print("Inspeccionando los primeros 5 LONG trades de ALPINE para verificar realismo:")
    verify_backtest_v3("ALPINEUSDT", max_inspect=5)
