"""
OPTIMIZADOR DE EXHAUSTIÓN (FAN-HUNTER)
=====================================
Prueba diferentes umbrales de RSI, confirmación de velas 
y gestión de Trailing Stop para maximizar el Net Profit real.
Descuenta fees de Binance Futures (0.1% total round-trip).
"""
import pandas as pd
import numpy as np
import os
import itertools

DATA_DIR = r"C:\CHACAL_ZERO_FRICTION\research_data"
FEE_ROUND_TRIP = 0.10  # 0.05% entrar + 0.05% salir

def load_data(symbol):
    file_path = os.path.join(DATA_DIR, f"{symbol}_1m_recent.csv")
    if not os.path.exists(file_path):
        return None
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # 1. Indicadores Base
    df['vol_mean'] = df['volume'].rolling(window=1440).mean()
    df['vol_std'] = df['volume'].rolling(window=1440).std()
    df['z_score'] = (df['volume'] - df['vol_mean']) / df['vol_std']
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 2. Confirmación de Velas
    df['is_bearish'] = df['close'] < df['open']
    return df

def simulate_short_strategy(df, rsi_entry, use_bear_confirm, tp, sl, ts_act, ts_offset):
    # Encontramos los índices donde la condición de entrada es CIERTA
    cond_rsi = df['rsi'].values > rsi_entry
    cond_bear = df['is_bearish'].values if use_bear_confirm else np.ones(len(df), dtype=bool)
    signal_indices = np.where(cond_rsi & cond_bear)[0]
    
    # Filtramos para asegurarnos de que empiezan después de la fila 1440
    signal_indices = signal_indices[signal_indices >= 1440]
    
    trades = []
    
    # Operaciones vectorizadas - arrays para acceso rápido
    closes = df['close'].values
    rsis = df['rsi'].values
    max_idx = len(closes)
    
    i = 0
    while i < len(signal_indices):
        entry_idx = signal_indices[i]
        entry_price = closes[entry_idx]
        
        highest_profit = 0.0
        
        # Simular trade desde entry_idx
        for j in range(entry_idx + 1, max_idx):
            current_price = closes[j]
            current_rsi = rsis[j]
            
            current_profit = (entry_price - current_price) / entry_price * 100
            if current_profit > highest_profit:
                highest_profit = current_profit
            
            close_trade = False
            
            # SL
            if current_profit <= -sl:
                close_trade = True
            # TP
            elif current_profit >= tp and highest_profit < ts_act:
                close_trade = True
            # TS
            elif highest_profit >= ts_act and current_profit <= highest_profit - ts_offset:
                close_trade = True
            # RSI revert
            elif current_rsi < 45:
                close_trade = True
                
            if close_trade:
                trades.append(current_profit - FEE_ROUND_TRIP)
                
                # Avanzar la 'i' en signal_indices para no reentrar al mismo trade o mientras estábamos en posición
                while i < len(signal_indices) and signal_indices[i] <= j:
                    i += 1
                break
        else:
            # Llegamos al final del dataframe sin cerrar, avanzamos i
            i += 1
            
    if not trades:
        return 0, 0
    return np.sum(trades), len(trades)

def optimize(symbol):
    df = load_data(symbol)
    if df is None: return
    
    # Espacio de búsqueda
    rsi_levels = [80, 83, 85, 87, 90]
    bear_confirms = [False, True]
    tps = [2.0, 3.0, 5.0]
    sls = [2.0, 3.0, 4.0]
    # TS [activar, retroceso]
    ts_configs = [(1.5, 0.5), (2.0, 1.0), (3.0, 1.0)] 
    
    results = []
    
    print(f"\nOptimizando {symbol} (Total comb: {len(rsi_levels)*len(bear_confirms)*len(tps)*len(sls)*len(ts_configs)})")
    
    for rsi, bear, tp, sl, (ts_a, ts_o) in itertools.product(rsi_levels, bear_confirms, tps, sls, ts_configs):
        net, count = simulate_short_strategy(df, rsi, bear, tp, sl, ts_a, ts_o)
        if count > 50: # Mínimo de trades para significancia estadística
            results.append({
                'rsi_in': rsi,
                'bear_cf': bear,
                'tp': tp,
                'sl': sl,
                'ts_act': ts_a,
                'ts_off': ts_o,
                'net_prof': net,
                'trades': count,
                'avg': net/count if count > 0 else 0
            })
            
    res_df = pd.DataFrame(results)
    if res_df.empty:
        print("No valid parameter combinations found.")
        return
        
    top_5 = res_df.sort_values('net_prof', ascending=False).head(5)
    print("\nTOP 5 CONFIGURACIONES (NET PROFIT REAL POST-FEES):")
    print(top_5.to_string(index=False))

if __name__ == "__main__":
    optimize("ALPINEUSDT")
    optimize("SANTOSUSDT")
