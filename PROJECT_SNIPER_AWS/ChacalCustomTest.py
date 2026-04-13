import pandas as pd
import numpy as np
import os

DATA_PATH = '/mnt/c/CHACAL_ZERO_FRICTION/PROJECT_SNIPER_AWS/user_data/data/binance'

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

def run_test():
    try:
        btc_1h = pd.read_feather(os.path.join(DATA_PATH, "BTC_USDT_USDT-1h-futures.feather"))
    except Exception as e:
        print(f"Error loading data: {e}")
        return
        
    btc_1h.columns = [c.lower() for c in btc_1h.columns]
    btc_1h['date'] = pd.to_datetime(btc_1h['date'], utc=True)
    btc_1h['ema50'] = ema_pure(btc_1h['close'], 50)
    btc_1h['atr_btc'] = atr_pure(btc_1h, 14)
    btc_1h['atr_btc_mean'] = btc_1h['atr_btc'].rolling(8).mean()
    df_btc = btc_1h[['date', 'ema50', 'atr_btc', 'atr_btc_mean', 'close']].rename(columns={'close':'btc_close'}).copy()

    meses = [5, 6, 7, 8]
    paquetes = ["SOL/USDT:USDT", "ETH/USDT:USDT", "BTC/USDT:USDT", "LINK/USDT:USDT", "AVAX/USDT:USDT", "BNB/USDT:USDT", "XRP/USDT:USDT"]
    
    # Pruebas con diferentes configuraciones
    configs = [
        {"name": "ACTUAL (Bloqueado)", "vol_mult": 1.44, "rsi_thresh": 32, "adx_req": 26, "lat_lim": 0.043},
        {"name": "RELAJADO (Tierra Media)", "vol_mult": 1.15, "rsi_thresh": 40, "adx_req": 20, "lat_lim": 0.025}
    ]
    
    print("\n🦅 --- BACKTEST: TEST DE ANSIEDAD (FLEXIBILIZANDO EL SNIPER BEAR) ---")
    
    for cfg in configs:
        global_trades = 0
        global_profit = 0
        print(f"\n>> CONFIG: {cfg['name']} | VolMult: {cfg['vol_mult']} | RSI<{cfg['rsi_thresh']} | Umbral LAT: {cfg['lat_lim']*100}%")
        
        for mes in meses:
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
                
                # ADX simulado = volatilidad simple > algo (el ADX es lento en pandas regular)
                # Lo obviaremos para ver solo RSI y Volumen
                
                # LÓGICA TIPO SNIPER BEAR
                # master_bear_switch = (df['btc_close'] < df['ema50']) & (df['atr_btc'] > df['atr_btc_mean'])
                # En la version relajada, si lat_lim es mas chico, el orchestrator pasa el control a "Fox" o a "Bear" mas rapido.
                # Como probamos a Sniper Bear, asumimos que dispara cuando:
                # btc esta debajo de EMA50 (sin importar el ATR para la prueba relajada, para ver si genera trades!)
                # O si respetamos el ATR:
                btc_vol = df['atr_btc'] > df['atr_btc_mean'] if cfg['name'] == "ACTUAL (Bloqueado)" else True
                
                short_cond = (
                    (df['btc_close'] < df['ema50']) & btc_vol &
                    (df['volume'] > (df['vol_mean'] * cfg['vol_mult'])) &
                    (df['price_change'] < -0.001) &
                    (df['rsi'] < cfg['rsi_thresh']) &
                    (df['close'] < df['bb_mid'])
                )
                
                in_trade = False
                entry_p = 0
                for i, row in df.iterrows():
                    if not in_trade:
                        if short_cond[i]:
                            in_trade = True
                            entry_p = row['close']
                            mes_trades += 1
                    else:
                        p = (entry_p - row['close']) / entry_p
                        if p >= 0.045 or p <= -0.09:
                            global_profit += p * 7.0 # Leverage 7x
                            in_trade = False
            
            global_trades += mes_trades
        
        print(f"Total Trades 4 meses: {global_trades} | Profit Estimado: {global_profit*100:.2f}%")

if __name__ == "__main__":
    run_test()
