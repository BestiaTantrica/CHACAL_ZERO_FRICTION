
import pandas as pd
import numpy as np
import os

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

def ver_trades():
    print("📡 CARGANDO RADIOGRAFÍA DE TRADES DE DE MAYO EN SOL/USDT...")
    
    btc_1h = pd.read_feather(os.path.join(DATA_PATH, "BTC_USDT_USDT-1h-futures.feather"))
    btc_1h.columns = [c.lower() for c in btc_1h.columns]
    btc_1h['date'] = pd.to_datetime(btc_1h['date'], utc=True)
    btc_1h['ema50'] = ema_pure(btc_1h['close'], 50)
    btc_1h['atr_btc'] = atr_pure(btc_1h, 14)
    btc_1h['atr_btc_mean'] = btc_1h['atr_btc'].rolling(8).mean()
    btc_1h['rsi_btc_1h'] = rsi_pure(btc_1h['close'], 14)
    df_btc = btc_1h[['date', 'ema50', 'rsi_btc_1h', 'atr_btc', 'atr_btc_mean', 'close']].rename(columns={'close':'btc_close'}).copy()

    file_path = os.path.join(DATA_PATH, "SOL_USDT_USDT-5m-futures.feather")
    df = pd.read_feather(file_path)
    df.columns = [c.lower() for c in df.columns]
    df['date'] = pd.to_datetime(df['date'], utc=True)
    df = pd.merge(df, df_btc, on='date', how='left').ffill()
    
    df = df[df['date'].dt.month == 5].reset_index(drop=True)
    
    df['rsi'] = rsi_pure(df['close'], 14)
    df['price_change'] = df['close'].pct_change()
    df['bb_mid'] = df['close'].rolling(20).mean()
    df['vol_mean'] = df['volume'].rolling(20).mean()
    
    # LA LÓGICA DE TU ESTRATEGIA (Triple Selector)
    df['master_bear_switch'] = ((df['btc_close'] < df['ema50']) & (df['atr_btc'] > df['atr_btc_mean'])).astype(int)
    
    df['market_regime'] = 0
    df.loc[(df['master_bear_switch'] == 1) & (df['rsi_btc_1h'] >= 40), 'market_regime'] = 1             # Lateral Bear
    df.loc[(df['master_bear_switch'] == 1) & (df['rsi_btc_1h'] < 40) & (df['rsi_btc_1h'] >= 20), 'market_regime'] = 2 # Bear Normal
    df.loc[(df['master_bear_switch'] == 1) & (df['rsi_btc_1h'] < 20), 'market_regime'] = 3                # Super Bear

    pulse = 0.001
    base = (df['price_change'] < -pulse) & (df['close'] < df['bb_mid']) & (df['rsi'] < 45)

    # Entradas por modo
    lat_entry = base & (df['market_regime'] == 1) & (df['volume'] > df['vol_mean'] * 2.8) & (df['rsi'] < 25)
    bear_entry = base & (df['market_regime'] == 2) & (df['volume'] > df['vol_mean'] * 1.44) & (df['rsi'] < 32)
    entries = lat_entry | bear_entry

    trades = []
    in_trade = False
    
    for i, row in df.iterrows():
        if not in_trade:
            if entries[i]:
                in_trade = True
                entry_date = row['date']
                entry_price = row['close']
                modo_entrada = row['market_regime']
                rsi_btc = row['rsi_btc_1h']
        else:
            profit = (entry_price - row['close']) / entry_price
            if profit >= 0.045 or profit <= -0.09:
                resultado = "✅ WIN (+4.5%)" if profit > 0 else "❌ LOSS (-9%)"
                trades.append({
                    'FECHA ENTRADA': entry_date.strftime('%Y-%m-%d %H:%M'),
                    'DURACION': str(row['date'] - entry_date),
                    'MODO DEL BOT': f"Modo {int(modo_entrada)}",
                    'RSI BTC (Selector)': f"{rsi_btc:.1f}",
                    'RESULTADO': resultado
                })
                in_trade = False

    t_df = pd.DataFrame(trades)
    print("\n" + "="*80)
    print(" █ DATOS PUROS Y DUROS: TODOS LOS TRADES DE MAYO EN SOL/USDT (Vela x Vela) █")
    print("="*80)
    if not t_df.empty:
        print(t_df.to_string(index=False))
    else:
        print("No hubieron trades.")
    print("="*80 + "\n")

if __name__ == "__main__":
    ver_trades()
