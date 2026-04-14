import pandas as pd
import json
import os

def analyze_btc_bands(btc_path):
    if not os.path.exists(btc_path):
        print(f"No se encontró {btc_path}")
        return

    # Leer Feather
    df = pd.read_feather(btc_path)
    # Nombre de columnas en feather de freqtrade: date, open, high, low, close, volume
    
    # Simular EMA50 1h
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['dist'] = (df['close'] - df['ema50']) / df['ema50']
    
    # Rangos del usuario:
    # Banda Positiva: 1.9% a 3.9%
    # Banda Negativa: -1.9% a -3.9%
    
    pos_band = df[(df['dist'] >= 0.019) & (df['dist'] <= 0.039)]
    neg_band = df[(df['dist'] <= -0.019) & (df['dist'] >= -0.039)]
    
    total_samples = len(df)
    print(f"Archivo: {btc_path}")
    print(f"Total velas analizadas: {total_samples}")
    print(f"Velas en Zona Relevo POS (1.9% a 3.9%): {len(pos_band)} ({len(pos_band)/total_samples*100:.2f}%)")
    print(f"Velas en Zona Relevo NEG (-1.9% a -3.9%): {len(neg_band)} ({len(neg_band)/total_samples*100:.2f}%)")
    
    print("\n--- CONCLUSIÓN TEÓRICA ---")
    total_relevo = len(pos_band) + len(neg_band)
    if total_relevo > 0:
        print(f"El bot Lateral pasaría el { total_relevo/total_samples*100:.2f}% de su vida en la 'Zona de Salto'.")
        print("Teoría: Si BTC está aquí, el mercado está TENSO. Si el bot entra, está apostando a que no explotará.")
        print("Si el winrate en esta zona es malo, significa que el 'Lateral' no debe tocarla.")
    else:
        print("BTC rara vez se queda en ese 'limbo'. Suele atravesarlo rápido o no llegar.")

if __name__ == "__main__":
    path = r"C:\CHACAL_ZERO_FRICTION\LAB_BACKTEST_ANUAL\user_data\data\binance\futures\BTC_USDT_USDT-1h-futures.feather"
    analyze_btc_bands(path)
