
import pandas as pd
import numpy as np
import os

# =========================================================================
# CHACAL BACKTESTER v4.0 - SIMULADOR FIEL TRIPLE-MODO
# Este backtester NO altera tu ADN, simplemente mide la lógica 
# exacta de ChacalTripleMode.py en los meses descargados.
# =========================================================================

DATA_PATH = r'user_data/data/binance/futures'

def rsi_pure(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0); down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    return 100 - (100 / (1 + (ema_up / ema_down)))

def atr_pure(df, period=14):
    tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def ema_pure(series, period=50):
    return series.ewm(span=period, adjust=False).mean()

def run_stress_test(leverage=5.0):
    # CARGAR DATOS BTC (Radar)
    try:
        btc_1h = pd.read_feather(os.path.join(DATA_PATH, "BTC_USDT_USDT-1h-futures.feather"))
    except FileNotFoundError:
        print("❌ Error: No se encontraron los datos de BTC 1h. Asegurate de que descargó bien.")
        return

    btc_1h.columns = [c.lower() for c in btc_1h.columns]
    btc_1h['date'] = pd.to_datetime(btc_1h['date'], utc=True)
    btc_1h['ema50'] = ema_pure(btc_1h['close'], 50)
    btc_1h['atr_btc'] = atr_pure(btc_1h, 14)
    btc_1h['atr_btc_mean'] = btc_1h['atr_btc'].rolling(8).mean()
    btc_1h['rsi_btc'] = rsi_pure(btc_1h['close'], 14)
    
    df_btc = btc_1h[['date', 'ema50', 'rsi_btc', 'atr_btc', 'atr_btc_mean', 'close']].rename(columns={'close':'btc_close'}).copy()

    meses = [5, 6, 7, 8]
    paquetes = ["SOL/USDT:USDT", "ETH/USDT:USDT", "BTC/USDT:USDT", "LINK/USDT:USDT", "AVAX/USDT:USDT", "ADA/USDT:USDT", "XRP/USDT:USDT"]
    
    global_profit = 0
    
    print("\n🦅 --- CHACAL LAB: VALIDACIÓN DEL TRIPLE SELECTOR DE RÉGIMEN ---")
    print("Midiendo fielmente la lógica de ChacalTripleMode.py mes a mes.")
    print(f"{'MES':<6} | {'TRADES':<8} | {'PROFIT (%)':<12} | {'SITUACIÓN'}")
    print("-" * 50)
    
    for mes in meses:
        mes_profit = 0
        mes_trades = 0
        
        for pair in paquetes:
            file_path = os.path.join(DATA_PATH, f"{pair.replace('/', '_').replace(':', '_')}-5m-futures.feather")
            if not os.path.exists(file_path): continue
            
            df = pd.read_feather(file_path)
            df.columns = [c.lower() for c in df.columns]
            df['date'] = pd.to_datetime(df['date'], utc=True)
            df = pd.merge(df, df_btc, on='date', how='left').ffill()
            df = df[df['date'].dt.month == mes].reset_index(drop=True)
            if df.empty: continue
            
            df['rsi'] = rsi_pure(df['close'], 14)
            df['price_change'] = df['close'].pct_change()
            df['bb_mid'] = df['close'].rolling(20).mean()
            df['vol_mean'] = df['volume'].rolling(20).mean()
            
            # --- EVALUACIÓN EXACTA DE ChacalTripleMode.py ---
            
            # Master Bear Switch
            df['btc_under_ema50'] = df['btc_close'] < df['ema50']
            df['btc_vol_activa']  = df['atr_btc'] > df['atr_btc_mean']
            df['master_bear_switch'] = (df['btc_under_ema50'] & df['btc_vol_activa']).astype(int)
            
            bear_active = df['master_bear_switch'] == 1
            btc_rsi = df['rsi_btc']

            # Pivotes de la estrategia real
            sb_thresh = 20
            bear_thresh = 40

            df['market_regime'] = 0
            df.loc[bear_active & (btc_rsi >= bear_thresh), 'market_regime'] = 1             # Lateral Bear
            df.loc[bear_active & (btc_rsi < bear_thresh) & (btc_rsi >= sb_thresh), 'market_regime'] = 2 # Bear Normal
            df.loc[bear_active & (btc_rsi < sb_thresh), 'market_regime'] = 3                # Super Bear

            # Condición Base (La misma de la estrategia)
            pulse = 0.001
            base = (
                (df['price_change'] < -pulse) &
                (df['close'] < df['bb_mid']) &
                (df['rsi'] < 45)
            )

            # Lógica por Modo (Los números de la estrategia)
            # MODO 1: Lateral (v_factor 2.8, rsi_entry 25)
            lat_entry = base & (df['market_regime'] == 1) & (df['volume'] > df['vol_mean'] * 2.8) & (df['rsi'] < 25)
            
            # MODO 2: Bear Normal (v_factor 1.44, rsi_entry 32)
            bear_entry = base & (df['market_regime'] == 2) & (df['volume'] > df['vol_mean'] * 1.44) & (df['rsi'] < 32)
            
            # MODO 3: Super Bear (v_factor 1.44, rsi_entry 32) -> Fiel a lo último restaurado
            sb_entry = base & (df['market_regime'] == 3) & (df['volume'] > df['vol_mean'] * 1.44) & (df['rsi'] < 32)

            entries = lat_entry | bear_entry | sb_entry

            in_trade = False
            entry_p = 0
            
            for i, row in df.iterrows():
                if not in_trade:
                    if entries[i]:
                        in_trade = True
                        entry_p = row['close']
                        mes_trades += 1
                else:
                    p = (entry_p - row['close']) / entry_p
                    if p >= 0.045 or p <= -0.09:
                        mes_profit += p * leverage
                        in_trade = False
        
        global_profit += mes_profit
        situacion = "Lateral/Alcista" if mes in [5,6] else "Bear Inicial" if mes == 7 else "Crash Severo"
        print(f"{mes:<6} | {mes_trades:<8} | {mes_profit*100:>10.2f}% | {situacion}")

    print("-" * 50)
    print(f"💎 RESULTADO (MODOS 1, 2 Y 3 EN ACCIÓN): {global_profit*100:.2f}%")
    print("Midiendo la lógica sin alterar los parámetros de la estrategia.")
    print("█" * 50 + "\n")

if __name__ == "__main__":
    run_stress_test()
