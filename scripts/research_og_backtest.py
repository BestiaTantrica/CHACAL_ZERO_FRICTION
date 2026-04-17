import pandas as pd
import numpy as np
import os

DATA_DIR = r"C:\CHACAL_ZERO_FRICTION\research_data"

def run_backtest_fan_token(symbol):
    file_path = os.path.join(DATA_DIR, f"{symbol}_1h_full.csv")
    if not os.path.exists(file_path):
        print(f"Error: No hay datos para {symbol}")
        return

    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # Parámetros del modelo
    PUMP_THRESHOLD = 7.0  # % de crecimiento para considerar pump
    REVERSION_HOURS = 4   # Horas a esperar para recoger beneficios del short
    
    # Identificar señales
    df['pump_mag'] = (df['high'] - df['open']) / df['open'] * 100
    pumps = df[df['pump_mag'] >= PUMP_THRESHOLD].index
    
    total_long_profit = 0
    total_short_profit = 0
    trades_count = len(pumps)
    
    if trades_count == 0:
        print(f"No se detectaron trades para {symbol} con el umbral del {PUMP_THRESHOLD}%")
        return

    for idx in pumps:
        # Simulación SHORT (Más realista): 
        # Vendemos en el High de la vela del pump (asumiendo que detectamos la ignición)
        # Compramos N horas después
        if idx + REVERSION_HOURS < len(df):
            price_entry_short = df.loc[idx, 'high']
            price_exit_short = df.loc[idx + REVERSION_HOURS, 'close']
            profit_short = (price_entry_short - price_exit_short) / price_entry_short * 100
            total_short_profit += profit_short
            
        # Simulación LONG (Conservative):
        # Compramos a la apertura de la vela de ignición 
        # Cerramos al High (asumiendo Take Profit dinámico)
        profit_long = df.loc[idx, 'pump_mag']
        total_long_profit += profit_long

    avg_short = total_short_profit / trades_count
    avg_long = total_long_profit / trades_count
    
    print(f"\n--- BACKTEST MACRO: {symbol} ---")
    print(f"Total eventos: {trades_count}")
    print(f"Profit acumulado LONG (Pump): {total_long_profit:.2f}% (Avg: {avg_long:.2f}%)")
    print(f"Profit acumulado SHORT (Reversión): {total_short_profit:.2f}% (Avg: {avg_short:.2f}%)")
    
    return {
        "symbol": symbol,
        "trades": trades_count,
        "long_pct": total_long_profit,
        "short_pct": total_short_profit
    }

if __name__ == "__main__":
    symbols = ["OGUSDT", "SANTOSUSDT", "LAZIOUSDT", "ALPINEUSDT"]
    results = []
    for s in symbols:
        res = run_backtest_fan_token(s)
        if res:
            results.append(res)
    
    if results:
        rdf = pd.DataFrame(results)
        print("\n=== RESUMEN GLOBAL FAN-HUNTER ===")
        print(f"Total Trades analizados: {rdf['trades'].sum()}")
        print(f"Rentabilidad Teórica Total (Sin apalancar): {(rdf['long_pct'].sum() + rdf['short_pct'].sum()):.2f}%")
