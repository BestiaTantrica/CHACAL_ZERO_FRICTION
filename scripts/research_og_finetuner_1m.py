import pandas as pd
import numpy as np
import os

DATA_DIR = r"C:\CHACAL_ZERO_FRICTION\research_data"

def backtest_1m_fino(symbol, z_threshold=4.0, target_profit=5.0, stop_loss=3.0):
    file_path = os.path.join(DATA_DIR, f"{symbol}_1m_recent.csv")
    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # 1. Indicadores Milimétricos
    df['vol_mean'] = df['volume'].rolling(window=1440).mean()
    df['vol_std'] = df['volume'].rolling(window=1440).std()
    df['z_score'] = (df['volume'] - df['vol_mean']) / df['vol_std']
    
    # RSI (para evitar comprar tarde)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 2. Lógica de Simulación
    in_position = False
    entry_price = 0
    trades = []
    
    for i in range(1440, len(df)):
        row = df.iloc[i]
        
        if not in_position:
            # GATILLO: Ignición extrema + No sobrecomprado
            if row['z_score'] > z_threshold and row['rsi'] < 70:
                in_position = True
                entry_price = row['close']
                entry_date = row['date']
        else:
            # GESTIÓN DE SALIDA
            current_profit = (row['close'] - entry_price) / entry_price * 100
            
            # Take Profit o Stop Loss
            if current_profit >= target_profit or current_profit <= -stop_loss:
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': row['date'],
                    'profit': current_profit
                })
                in_position = False
                
    if not trades:
        return {'symbol': symbol, 'net_profit': 0, 'trades_count': 0}

    tdf = pd.DataFrame(trades)
    return {
        'symbol': symbol,
        'net_profit': tdf['profit'].sum(),
        'trades_count': len(tdf),
        'win_rate': (tdf['profit'] > 0).mean() * 100,
        'avg_profit': tdf['profit'].mean()
    }

if __name__ == "__main__":
    symbols = ["OGUSDT", "SANTOSUSDT"] # Los que ya tienen 1m bajado
    results = []
    
    print("--- OPTIMIZACION DE 'EL FINO' V2 (Restrictiva) ---")
    print("Probando: Z-Score > 8.0 | Entry RSI < 70 | Target: 5% | SL: 4%")
    
    for s in symbols:
        res = backtest_1m_fino(s, z_threshold=8.0, target_profit=5.0, stop_loss=4.0)
        if res:
            results.append(res)
            print(f"\nResultados {s}:")
            print(f" - Net Profit: {res['net_profit']:.2f}%")
            print(f" - Trades: {res['trades_count']}")
            print(f" - WinRate: {res['win_rate']:.1f}%")
            print(f" - Avg Profit: {res['avg_profit']:.2f}%")
