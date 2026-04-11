import pandas as pd
import json
import glob
import os

def load_backtest_trades(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    # Freqtrade backtest result structure has trades in 'strategy' -> 'strategy_name' -> 'trades'
    strategy_name = list(data['strategy'].keys())[0]
    trades = data['strategy'][strategy_name]['trades']
    df = pd.DataFrame(trades)
    df['open_date'] = pd.to_datetime(df['open_date'])
    df['close_date'] = pd.to_datetime(df['close_date'])
    return df, strategy_name

def analyze_trifasico_regime(lateral_file, sniper_file):
    print("--- SINTETIZADOR TRIFÁSICO CHACAL ---")
    
    lateral_trades, lat_name = load_backtest_trades(lateral_file)
    sniper_trades, sni_name = load_backtest_trades(sniper_file)
    
    # Marcamos origen
    lateral_trades['specialist'] = 'LATERAL'
    sniper_trades['specialist'] = 'SNIPER'
    
    # Unificamos
    all_trades = pd.concat([lateral_trades, sniper_trades]).sort_values('open_date')
    
    # Cálculo de Equity Acumulada (simplificado)
    total_profit = all_trades['profit_abs'].sum()
    total_trades = len(all_trades)
    
    print(f"Trades Totales: {total_trades}")
    print(f"Profit Neto Combinado: {total_profit:.2f} USDT")
    
    # Análisis de Junio 2024 (Cambio de Régimen)
    junio_trades = all_trades[(all_trades['open_date'] >= '2024-06-01') & (all_trades['open_date'] <= '2024-06-30')]
    
    print("\nDetalle Junio 2024 (Fase Crítica):")
    lat_junio = junio_trades[junio_trades['specialist'] == 'LATERAL']
    sni_junio = junio_trades[junio_trades['specialist'] == 'SNIPER']
    
    print(f" - Lateral Hunter (Junio): {lat_junio['profit_abs'].sum():.2f} USDT ({len(lat_junio)} trades)")
    print(f" - Sniper Bear (Junio):    {sni_junio['profit_abs'].sum():.2f} USDT ({len(sni_junio)} trades)")
    print(f" - RESULTADO NETO RELEVO:  {(lat_junio['profit_abs'].sum() + sni_junio['profit_abs'].sum()):.2f} USDT")

    if (sni_junio['profit_abs'].sum() > abs(lat_junio['profit_abs'].sum())) and lat_junio['profit_abs'].sum() < 0:
        print("\n✅ ÉXITO: El Sniper Bear recuperó las pérdidas por breakout del Lateral Hunter.")
    else:
        print("\n⚠️ ALERTA: Revisar sensibilidad de activación del Sniper Bear.")

if __name__ == "__main__":
    # Estos archivos deben existir tras correr los backtests
    LAT_RESULT = "c:/CHACAL_ZERO_FRICTION/CHACAL_LATERAL/user_data/backtest_results/backtest-result-lateral_V4.json"
    SNI_RESULT = "c:/CHACAL_ZERO_FRICTION/PROJECT_SNIPER_AWS/user_data/backtest_results/backtest-result-sniper_ultra.json"
    
    if os.path.exists(LAT_RESULT) and os.path.exists(SNI_RESULT):
        analyze_trifasico_regime(LAT_RESULT, SNI_RESULT)
    else:
        print("Error: Archivos de resultados no encontrados. Ejecute los backtests primero.")
