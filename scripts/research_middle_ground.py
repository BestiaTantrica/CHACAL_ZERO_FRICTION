"""
OPTIMIZADOR: EL PUNTO MEDIO (Frecuencia vs Rentabilidad)
======================================================
Busca un balance donde haya al menos 1 trade por día por moneda (~180 trades en 6 meses)
pero con suficiente recorrido de caída (>2%) para absorber comisiones.
"""
import pandas as pd
import numpy as np
import os

DATA_DIR = r"C:\CHACAL_ZERO_FRICTION\research_data"
FEE_ROUND_TRIP = 0.10  # 0.10% total fee de futures

def simulate_middle_ground(symbol, pump_req=3.0, rsi_entry=85, tp=2.5, sl=4.0):
    file_path = os.path.join(DATA_DIR, f"{symbol}_1m_recent.csv")
    if not os.path.exists(file_path):
        return None
    df = pd.read_csv(file_path)
    # df['date'] = pd.to_datetime(df['date'])
    
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    
    # 1. RSI
    delta = pd.Series(closes).diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsis = (100 - (100 / (1 + rs))).values
    
    # 2. Requisito de PUMP previo (ej: el precio saltó X% en los últimos 60 minutos)
    df['min_60'] = df['low'].rolling(60).min()
    pump_magnitude = ((df['close'] - df['min_60']) / df['min_60'] * 100).values
    
    in_position = False
    entry_price = 0.0
    trades = []
    
    for i in range(1440, len(closes)):
        if not in_position:
            # GATILLO: Hubo un pump agresivo (>3%) Y el RSI está agotado
            if rsis[i] > rsi_entry and pump_magnitude[i] > pump_req:
                in_position = True
                entry_price = closes[i]
                highest_profit = 0.0
        else:
            current_profit = (entry_price - closes[i]) / entry_price * 100
            if current_profit > highest_profit:
                 highest_profit = current_profit
                 
            # Salidas simples
            if current_profit <= -sl:
                trades.append(current_profit - FEE_ROUND_TRIP)
                in_position = False
            elif current_profit >= tp:
                trades.append(current_profit - FEE_ROUND_TRIP)
                in_position = False
            elif rsis[i] < 45: # Salida por enfriamiento
                trades.append(current_profit - FEE_ROUND_TRIP)
                in_position = False

    if not trades:
        return {'symbol': symbol, 'trades': 0, 'net': 0}
        
    trades_arr = np.array(trades)
    return {
        'symbol': symbol,
        'trades': len(trades_arr),
        'net_prof': np.sum(trades_arr),
        'win_rate': np.mean(trades_arr > 0) * 100,
        'avg': np.mean(trades_arr)
    }

if __name__ == "__main__":
    symbols = ["OGUSDT", "SANTOSUSDT", "LAZIOUSDT", "ALPINEUSDT"]
    
    # Parámetros del punto medio:
    # pump_req = 3% (Exigimos que haya subido un 3% en la última hora)
    # tp = 2.0% (Buscamos un retroceso de 2% puro)
    # SL = 4.0%
    
    # Vamos a probar varios niveles de exigencia de Pump
    for p_req in [2.0, 3.0, 4.0]:
        print(f"\n--- PRUEBA: Exigiendo Pump Previo > {p_req}% ---")
        total_trades = 0
        total_net = 0
        
        for s in symbols:
            res = simulate_middle_ground(s, pump_req=p_req, rsi_entry=85, tp=2.0, sl=4.0)
            if res and res['trades'] > 0:
                print(f" {s:12} | Trades: {res['trades']:4} | Net: {res['net_prof']:6.2f}% | Avg: {res['avg']:5.2f}% | WR: {res['win_rate']:5.1f}%")
                total_trades += res['trades']
                total_net += res['net_prof']
        
        # 180 días de testeo. Frecuencia diaria = total_trades / (180 días)
        freq_diaria = total_trades / 180
        print(f" >> FRECUENCIA ECOSISTEMA: {freq_diaria:.1f} trades/dia | NET TOTAL ECOSISTEMA: {total_net:.2f}%")
