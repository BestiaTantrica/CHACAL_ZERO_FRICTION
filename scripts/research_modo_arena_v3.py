import pandas as pd
import numpy as np
import os

DATA_DIR = r"C:\CHACAL_ZERO_FRICTION\research_data"

def backtest_modo_arena(symbol):
    file_path = os.path.join(DATA_DIR, f"{symbol}_1m_recent.csv")
    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    df['day_name'] = df['date'].dt.day_name()
    
    # 1. Indicadores
    df['vol_mean'] = df['volume'].rolling(window=1440).mean()
    df['vol_std'] = df['volume'].rolling(window=1440).std()
    df['z_score'] = (df['volume'] - df['vol_mean']) / df['vol_std']
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 2. Simulación
    in_position = False
    pos_type = None # 'long' o 'short'
    entry_price = 0
    trades = []
    
    for i in range(1440, len(df)):
        row = df.iloc[i]
        
        # Filtro de día (Solo Viernes, Sábado, Domingo, Lunes - El bloque de impacto)
        # if row['day_name'] not in ['Friday', 'Saturday', 'Sunday', 'Monday']:
        #     continue

        if not in_position:
            # GATILLO LONG: Ignición de volumen (Z > 8) + No sobrecomprado
            if row['z_score'] > 8.0 and row['rsi'] < 65:
                in_position = True
                pos_type = 'long'
                entry_price = row['close']
                entry_date = row['date']
            
            # GATILLO SHORT: Agotamiento (RSI > 85) + Volumen bajando?
            # Solo shorteamos después de un pump (Z_score alto reciente)
            elif row['rsi'] > 85:
                in_position = True
                pos_type = 'short'
                entry_price = row['close']
                entry_date = row['date']
        else:
            # GESTIÓN
            if pos_type == 'long':
                profit = (row['close'] - entry_price) / entry_price * 100
                # Salida LONG: RSI > 80 o TP 8% o SL 4%
                if row['rsi'] > 80 or profit >= 8.0 or profit <= -4.0:
                    trades.append({'type': 'long', 'profit': profit, 'date': row['date']})
                    in_position = False
            else:
                profit = (entry_price - row['close']) / entry_price * 100
                # Salida SHORT: RSI < 50 o TP 5% o SL 3%
                if row['rsi'] < 50 or profit >= 5.0 or profit <= -3.0:
                    trades.append({'type': 'short', 'profit': profit, 'date': row['date']})
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
    symbols = ["OGUSDT", "SANTOSUSDT"]
    print("--- EVALUACION 'MODO ARENA' V3 (Dual Long/Short) ---")
    for s in symbols:
        res = backtest_modo_arena(s)
        if res:
            print(f"\n{s}:")
            print(f" - Net Profit Total: {res['net_profit']:.2f}%")
            print(f" - Profit LONG: {res['long_profit']:.2f}%")
            print(f" - Profit SHORT: {res['short_profit']:.2f}%")
            print(f" - WinRate: {res['win_rate']:.1f}% ({res['trades']} trades)")
